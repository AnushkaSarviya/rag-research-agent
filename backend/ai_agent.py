# backend/ai_agent.py

# Step 1: Setup API Keys
import os
import logging
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langchain_core.messages.ai import AIMessage
from langchain_core.messages import HumanMessage, SystemMessage
from typing import List
from backend.tools.retriever import retrieve
from backend.tools.summarizer import generate_grounded_answer
from backend.tool_router import decide_tool, ToolDecision

load_dotenv()

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")
OPEN_ROUTER_API_KEY = os.environ.get("OPEN_ROUTER_API_KEY")


def _format_chat_history(history: List[str]) -> str:
    """Format a list of strings (user messages) into a chat history string."""
    if not history:
        return "No previous conversation."
    return "\n".join([f"User: {msg}" for msg in history])


def _inject_memory(system_prompt: str, query: str, history: List[str], long_term_memory: str = "") -> str:
    """Inject memory and query into the system prompt if placeholders exist."""
    chat_history_str = _format_chat_history(history)

    # Check if placeholders exist to avoid KeyError if the user provided a custom prompt without them
    placeholders = {
        "query": query,
        "chat_history": chat_history_str,
        "long_term_memory": long_term_memory if long_term_memory else "No relevant document context found."
    }

    try:
        # Only format if at least one placeholder is present to avoid issues with curly braces in prompts
        if any(f"{{{k}}}" in system_prompt for k in placeholders.keys()):
            return system_prompt.format(**placeholders)
        return system_prompt
    except Exception as e:
        logger.warning(f"Failed to format system prompt: {e}")
        return system_prompt


# Step 2: Setup LLM & Tools
DEFAULT_SYSTEM_PROMPT = """
You are a Research & Summarization Agent.
Your tasks:
1. When user asks a research question, retrieve from ingested sources.
2. Summarize into structured notes: Key Insights, Pros/Cons, Actionable Items.
3. Include citations like [source: ID#chunk:N].
4. Be concise, factual, and professional.
"""


@tool
def research_tool(query: str) -> str:
    """Retrieve and generate a grounded answer from ingested sources."""
    retrieved = retrieve(query, top_k=5)
    if not retrieved:
        return "The answer is not available in the provided context."
    answer = generate_grounded_answer(query, retrieved)
    return answer


def _build_search_tool():
    """Build the Tavily web search tool."""
    if not TAVILY_API_KEY:
        raise ValueError("TAVILY_API_KEY not found in environment variables")
    return TavilySearchResults(max_results=2, api_key=TAVILY_API_KEY)


def _build_llm(provider: str, llm_id: str):
    """
    Build and return the appropriate LangChain LLM instance.

    Args:
        provider: "Groq" or "OpenRouter"
        llm_id:   The model identifier string.

    Returns:
        A LangChain chat model (ChatGroq or ChatOpenAI).
    """
    if provider == "Groq":
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        return ChatGroq(model=llm_id, groq_api_key=GROQ_API_KEY)

    elif provider == "OpenRouter":
        if not OPEN_ROUTER_API_KEY:
            raise ValueError("OPEN_ROUTER_API_KEY not found in environment variables")
        return ChatOpenAI(
            model=llm_id,
            api_key=OPEN_ROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1"
        )
    else:
        raise ValueError(
            f"Unsupported provider: {provider}. Must be 'Groq' or 'OpenRouter'"
        )


# ── Step 3a: Standard ReAct Agent (existing flow) ─────────────────────────────
def get_response_from_ai_agent(
    llm_id,
    query,
    system_prompt,
    provider,
    allow_search=False,
    conversation_history=None
):
    """
    Get response from AI agent using LangGraph ReAct loop.

    Args:
        llm_id: Model identifier
        query: Current user query
        system_prompt: System prompt for the agent
        provider: "Groq" or "OpenRouter"
        allow_search: Whether to enable Tavily web search tool
        conversation_history: Optional list of previous messages for context
    """
    llm = _build_llm(provider, llm_id)

    # Build tools list — always include RAG tool, optionally add web search
    tools = [research_tool]
    if allow_search:
        tools.append(_build_search_tool())

    # Use provided system_prompt or fallback to DEFAULT_SYSTEM_PROMPT
    raw_prompt = (
        system_prompt.strip()
        if system_prompt and system_prompt.strip()
        else DEFAULT_SYSTEM_PROMPT
    )

    effective_prompt = _inject_memory(raw_prompt, query, conversation_history or [])

    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=effective_prompt
    )

    # Build messages from conversation history if provided
    messages = []
    if conversation_history:
        for msg in conversation_history[:-1]:   # All but the last message
            if isinstance(msg, str):
                messages.append({"role": "user", "content": msg})

    # Add current query
    messages.append({"role": "user", "content": query})

    state = {"messages": messages}

    response = agent.invoke(state)
    response_messages = response.get("messages", [])
    ai_messages = [m.content for m in response_messages if isinstance(m, AIMessage)]

    if not ai_messages:
        return "No response generated from agent."

    return ai_messages[-1]


# ── Step 3b: Routed Agent (new flow with tool decision step) ───────────────────
def get_response_with_routing(
    llm_id: str,
    query: str,
    system_prompt: str,
    provider: str,
    allow_search: bool = False,
    conversation_history=None,
) -> dict:
    """
    Two-phase agent execution:
      Phase 1 — Tool Router: Ask the LLM to decide which tool (if any) to invoke.
      Phase 2 — Execution:   Run the chosen tool or fall back to direct LLM reply.

    Returns a dict containing:
        - tool_decision: {"tool": str, "input": str}
        - summary / pros_cons / action_items / citations  (structured response fields)
        - raw_response (str, when no structured tool is used)
    """
    llm = _build_llm(provider, llm_id)

    # ── Phase 1: Tool Routing ──────────────────────────────────────────────────
    decision: ToolDecision = decide_tool(query, llm, conversation_history=conversation_history)
    tool_name = decision.tool
    tool_input = decision.input

    logger.info(f"[Agent] Routing decision → tool={tool_name!r}, input={tool_input!r}")

    # ── Phase 2: Execute based on decision ────────────────────────────────────
    if tool_name == "web_search" and allow_search:
        # Tavily web search → feed results back through ReAct agent
        try:
            search_tool = _build_search_tool()
            search_results = search_tool.invoke(tool_input)
            # Summarise search results using a direct LLM call
            search_context = (
                f"Web search results for: '{tool_input}'\n\n"
                + str(search_results)
            )
            raw_prompt = (
                system_prompt.strip() if system_prompt and system_prompt.strip()
                else DEFAULT_SYSTEM_PROMPT
            )
            effective_prompt = _inject_memory(
                raw_prompt, query, conversation_history or [], long_term_memory=search_context
            )

            summary_messages = [
                SystemMessage(content=effective_prompt),
                HumanMessage(content=query),
            ]
            summary_resp = llm.invoke(summary_messages)

            citations = [f"Web search: {tool_input}"]

            # Prepare result with summary
            result = {
                "summary": [summary_resp.content],
                "pros_cons": {"pros": [], "cons": []},
                "action_items": [],
                "citations": citations,
            }
        except Exception as exc:
            logger.warning(f"[Agent] Web search failed: {exc}. Falling back to direct LLM.")
            tool_name = "no_tool"
            result = None

    elif tool_name == "research_tool":
        # Direct RAG retrieval + grounded answering
        retrieved = retrieve(tool_input, top_k=5)
        if not retrieved:
            result = {
                "summary": ["The answer is not available in the provided context."],
                "pros_cons": {"pros": [], "cons": []},
                "action_items": [],
                "citations": [],
            }
        else:
            # Inject RAG results into the system prompt for the final answer
            context_str = "\n".join([f"- {c.get('text')}" for c in retrieved])
            raw_prompt = (
                system_prompt.strip() if system_prompt and system_prompt.strip()
                else DEFAULT_SYSTEM_PROMPT
            )
            final_prompt = _inject_memory(
                raw_prompt, query, conversation_history or [], long_term_memory=context_str
            )

            messages = [
                SystemMessage(content=final_prompt),
                HumanMessage(content=query)
            ]
            final_resp = llm.invoke(messages)

            result = {
                "summary": [final_resp.content],
                "pros_cons": {"pros": [], "cons": []},
                "action_items": [],
                "citations": [c.get("source_id", "unknown") for c in retrieved],
            }

    else:
        # no_tool (or web_search disabled) → direct LLM response
        tool_name = "no_tool"
        result = None

    # ── Fallback: Direct LLM when no_tool ────────────────────────────────────
    if result is None:
        raw_prompt = (
            system_prompt.strip() if system_prompt and system_prompt.strip()
            else DEFAULT_SYSTEM_PROMPT
        )
        effective_prompt = _inject_memory(raw_prompt, query, conversation_history or [])

        messages = [SystemMessage(content=effective_prompt)]

        if conversation_history:
            for msg in conversation_history[:-1]:
                if isinstance(msg, str):
                    messages.append(HumanMessage(content=msg))

        messages.append(HumanMessage(content=query))
        llm_response = llm.invoke(messages)
        result = {
            "summary": [llm_response.content],
            "pros_cons": {"pros": [], "cons": []},
            "action_items": [],
            "citations": [],
        }

    # Attach routing metadata to the result
    result["tool_decision"] = {
        "tool": tool_name,
        "input": tool_input,
    }

    return result
