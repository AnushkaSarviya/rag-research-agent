#Step1: Setup API Key for groq and tavily
import os
from dotenv import load_dotenv
load_dotenv()
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
TAVILY_API_KEY = os.environ.get("TAVILY_API_KEY")
OPEN_ROUTER_API_KEY = os.environ.get("OPEN_ROUTER_API_KEY")

#Step2:Setup LLM & tools
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults
#gpt for openai_llm
from langchain_core.tools import tool
from backend.tools.retriever import retrieve
from backend.tools.summarizer import summarize_with_evidence

@tool
def research_tool(query: str) -> str:
    """Retrieve and summarize information from ingested sources with citations."""
    retrieved = retrieve(query, top_k=5)
    summary = summarize_with_evidence(retrieved)
    return str(summary)


search_tool = TavilySearchResults(
    max_results=2,
    api_key=TAVILY_API_KEY
)

#Step3: Setup AI Agent with Search Tool functionality
from langgraph.prebuilt import create_react_agent
from langchain_core.messages.ai import AIMessage

system_prompt = """
You are a Research & Summarization Agent.
Your tasks:
1. When user asks a research question, retrieve from ingested sources.
2. Summarize into structured notes: Key Insights, Pros/Cons, Actionable Items.
3. Include citations like [source: ID#chunk:N].
4. Be concise, factual, and professional.
"""


#Step5: Main Function
def get_response_from_ai_agent(llm_id, query, system_prompt, provider, conversation_history=None):
    """
    Get response from AI agent.
    
    Args:
        llm_id: Model identifier
        query: Current user query
        system_prompt: System prompt for the agent
        provider: "Groq" or "OpenRouter"
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

    tools = [research_tool]   # RAG tool instead of Tavily

    # Use provided system_prompt or fallback to default
    # Note: system_prompt parameter name conflicts with module-level variable
    effective_prompt = system_prompt if (system_prompt and system_prompt.strip()) else """
You are a Research & Summarization Agent.
Your tasks:
1. When user asks a research question, retrieve from ingested sources.
2. Summarize into structured notes: Key Insights, Pros/Cons, Actionable Items.
3. Include citations like [source: ID#chunk:N].
4. Be concise, factual, and professional.
"""

    agent = create_react_agent(
        model=llm,
        tools=tools,
        state_modifier=effective_prompt
    )

    # Build messages from conversation history if provided
    messages = []
    if conversation_history:
        # Add previous messages (alternating user/assistant if available)
        for i, msg in enumerate(conversation_history[:-1]):  # All but the last message
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