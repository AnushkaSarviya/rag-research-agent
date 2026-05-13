# backend/main.py

# Step 1: Setup Pydantic Model (Schema Validation)
import time
import logging
from pydantic import BaseModel
from typing import List, Optional
from fastapi import FastAPI
from backend.ai_agent import (
    get_response_from_ai_agent,
    get_response_with_routing,
    _build_llm,
)
from backend.tools.summarizer import summarize_with_evidence
from backend.tool_router import decide_tool, get_tool_descriptions


class RequestState(BaseModel):
    session_id: Optional[str] = "default"   # for tracking conversation history
    model_name: str
    model_provider: str
    system_prompt: str
    messages: List[str]   # chat history (list of user messages)
    allow_search: bool = False
    retrieved_chunks: Optional[List[dict]] = None
    use_tool_routing: bool = True   # NEW: enable/disable the tool router step


class DecideRequest(BaseModel):
    query: str
    model_name: str
    model_provider: str


# Step 2: Setup AI Agent from FrontEnd Request
ALLOWED_MODEL_NAMES = [
    "mixtral-8x7b-32768",
    "llama-3.3-70b-versatile",
    "meta-llama/llama-3.1-70b-instruct"
]

# ---- Memory store for chat history ----
conversation_history = {}   # {session_id: [messages...]}

# ---- Logging setup ----
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

app = FastAPI(
    title="LangGraph Research & Summarization Agent",
    description=(
        "Backend API for RAG Agent with chat, ingestion, structured summaries, "
        "and an explicit Tool Router that decides which tool to use before execution."
    ),
    version="1.2"
)


# ── /chat ─────────────────────────────────────────────────────────────────────
@app.post(
    "/chat",
    summary="Chat with the Research & Summarization Agent",
    description=(
        "Send user messages and get structured research summaries with citations. "
        "When `use_tool_routing=true` (default), the agent first decides which tool "
        "to invoke before executing, and returns the tool decision in the response."
    ),
    response_description="Structured summary from the agent"
)
def chat_endpoint(request: RequestState):
    """
    API Endpoint to interact with the Research & Summarization Agent.

    Modes:
    1. If 'retrieved_chunks' are provided → run RAG summarizer directly.
    2. If 'use_tool_routing=True' (default) → route through tool router first,
       then execute the selected tool.
    3. If 'use_tool_routing=False' → fall back to the original ReAct agent.
    """
    if request.model_name not in ALLOWED_MODEL_NAMES:
        return {"error": "Invalid model name. Kindly select a valid AI model"}

    try:
        # Track session & conversation history
        session_id = request.session_id or "default"
        if session_id not in conversation_history:
            conversation_history[session_id] = []
        conversation_history[session_id].extend(request.messages)

        llm_id = request.model_name
        query = request.messages[-1]  # take latest message only
        system_prompt = request.system_prompt
        provider = request.model_provider
        allow_search = request.allow_search

        # Logging start
        start = time.time()

        # ── Mode 1: Direct RAG from provided chunks ────────────────────────────
        if request.retrieved_chunks:
            response = summarize_with_evidence(request.retrieved_chunks)

        # ── Mode 2: Tool-Routed execution (new default) ────────────────────────
        elif request.use_tool_routing:
            history = conversation_history.get(session_id, [])[:-1]
            response = get_response_with_routing(
                llm_id=llm_id,
                query=query,
                system_prompt=system_prompt,
                provider=provider,
                allow_search=allow_search,
                conversation_history=history,
            )

        # ── Mode 3: Legacy ReAct agent (opt-out of routing) ───────────────────
        else:
            history = conversation_history.get(session_id, [])[:-1]
            plain_response = get_response_from_ai_agent(
                llm_id,
                query,
                system_prompt,
                provider,
                allow_search=allow_search,
                conversation_history=history,
            )
            response = {
                "summary": [plain_response],
                "pros_cons": {"pros": [], "cons": []},
                "action_items": [],
                "citations": [],
            }

        latency = round(time.time() - start, 2)
        logging.info(
            f"[Session={session_id}] Model={llm_id}, Latency={latency}s, "
            f"Query={query}, ToolRouting={request.use_tool_routing}"
        )

        # Add metadata
        response["latency"] = latency
        response["model_used"] = llm_id
        response["session_id"] = session_id

        return response

    except Exception as e:
        logging.error(f"Error in chat_endpoint: {e}", exc_info=True)
        return {"error": f"Backend error: {str(e)}"}


# ── /decide ────────────────────────────────────────────────────────────────────
@app.post(
    "/decide",
    summary="Run only the Tool Router",
    description=(
        "Given a query and model, run ONLY the tool-routing step and return "
        "which tool would be selected and with what cleaned input — without "
        "actually executing the tool or answering the question."
    ),
)
def decide_endpoint(request: DecideRequest):
    """
    Standalone tool-router endpoint.
    Returns the tool decision without executing anything.
    """
    if request.model_name not in ALLOWED_MODEL_NAMES:
        return {"error": "Invalid model name. Kindly select a valid AI model"}
    try:
        llm = _build_llm(request.model_provider, request.model_name)
        # Standalone router call usually doesn't have history context unless provided,
        # but we can check if there's any history for this query if session_id was added.
        # For now, we pass None or an empty list as it's a standalone test.
        decision = decide_tool(request.query, llm, conversation_history=[])
        return {
            "query": request.query,
            "tool": decision.tool,
            "input": decision.input,
            "available_tools": list(get_tool_descriptions().keys()),
        }
    except Exception as e:
        logging.error(f"Error in decide_endpoint: {e}", exc_info=True)
        return {"error": f"Backend error: {str(e)}"}


# ── /tools ─────────────────────────────────────────────────────────────────────
@app.get(
    "/tools",
    summary="List available tools and their descriptions",
    description="Returns the full tool registry used by the Tool Router.",
)
def list_tools():
    """Get the complete tool registry with names, descriptions, and input formats."""
    return {"tools": get_tool_descriptions()}


# ── /history ──────────────────────────────────────────────────────────────────
@app.get("/history/{session_id}", summary="Get chat history by session ID")
def get_history(session_id: str):
    """Fetch all past messages for a given session"""
    return {"session_id": session_id, "history": conversation_history.get(session_id, [])}


# ── /models ───────────────────────────────────────────────────────────────────
@app.get("/models", summary="List available models")
def list_models():
    """Get the list of models supported by this backend"""
    return {"available_models": ALLOWED_MODEL_NAMES}


# ── /health ───────────────────────────────────────────────────────────────────
@app.get("/health", summary="Health check")
def health_check():
    """Verify that the API is running"""
    return {"status": "ok", "service": "RAG Agent Backend v1.2", "tool_routing": "enabled"}


# ── /ingest ───────────────────────────────────────────────────────────────────
@app.post("/ingest", summary="Ingest document into vector store")
def ingest_document_endpoint(file_path: str):
    """
    Ingest a PDF or text file into the vector database.
    Note: In production, you'd want to handle file uploads via UploadFile.
    """
    from backend.tools.retriever import ingest_document
    try:
        result = ingest_document(file_path)
        return result
    except Exception as e:
        logging.error(f"Error ingesting document: {e}")
        return {"status": "error", "message": str(e)}


# Step 3: Run app & Explore Swagger UI Docs
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=9999)
