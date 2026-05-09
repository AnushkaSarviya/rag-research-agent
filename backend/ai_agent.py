# backend/ai_agent.py

# Step 1: Setup API Keys
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent
from langchain_core.messages.ai import AIMessage
from backend.tools.retriever import retrieve
from backend.tools.summarizer import summarize_with_evidence

load_dotenv()

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")
OPEN_ROUTER_API_KEY = os.environ.get("OPEN_ROUTER_API_KEY")

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
    """Retrieve and summarize information from ingested sources with citations."""
    retrieved = retrieve(query, top_k=5)
    summary = summarize_with_evidence(retrieved)
    return str(summary)


def _build_search_tool():
    """Build the Tavily web search tool."""
    if not TAVILY_API_KEY:
        raise ValueError("TAVILY_API_KEY not found in environment variables")
    return TavilySearchResults(max_results=2, api_key=TAVILY_API_KEY)


# Step 3: Main Function
def get_response_from_ai_agent(
    llm_id,
    query,
    system_prompt,
    provider,
    allow_search=False,
    conversation_history=None
):
    """
    Get response from AI agent.

    Args:
        llm_id: Model identifier
        query: Current user query
        system_prompt: System prompt for the agent
        provider: "Groq" or "OpenRouter"
        allow_search: Whether to enable Tavily web search tool
        conversation_history: Optional list of previous messages for context
    """
    if provider == "Groq":
        if not GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        llm = ChatGroq(
            model=llm_id,
            groq_api_key=GROQ_API_KEY
        )
    elif provider == "OpenRouter":
        if not OPEN_ROUTER_API_KEY:
            raise ValueError("OPEN_ROUTER_API_KEY not found in environment variables")
        llm = ChatOpenAI(
            model=llm_id,
            api_key=OPEN_ROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1"
        )
    else:
        raise ValueError(f"Unsupported provider: {provider}. Must be 'Groq' or 'OpenRouter'")

    # Build tools list — always include RAG tool, optionally add web search
    tools = [research_tool]
    if allow_search:
        tools.append(_build_search_tool())

    # Use provided system_prompt or fallback to DEFAULT_SYSTEM_PROMPT
    effective_prompt = system_prompt.strip() if system_prompt and system_prompt.strip() else DEFAULT_SYSTEM_PROMPT

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