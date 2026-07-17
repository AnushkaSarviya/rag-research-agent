# backend/main.py

# ─────────────────────────────────────────────────────────────────────────────
# Step 1: Imports & Setup
# ─────────────────────────────────────────────────────────────────────────────
import os
import time
import logging
from uuid import uuid4
from pathlib import Path

from pydantic import BaseModel
from typing import List, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File
from contextlib import asynccontextmanager

from backend.ai_agent import (
    get_response_from_ai_agent,
    get_response_with_routing,
    _build_llm,
)
from backend.tools.summarizer import summarize_with_evidence
from backend.tool_router import decide_tool, get_tool_descriptions
from backend.db import init_db, save_message, get_history, get_session_messages_as_list


# ─────────────────────────────────────────────────────────────────────────────
# Upload safety constants
#
# WHY these constraints?
# ──────────────────────
# MAX_UPLOAD_SIZE: A 20 MB cap prevents denial-of-service via huge uploads
#   that exhaust memory (FastAPI reads UploadFile into a SpooledTemporaryFile,
#   but we still need to write it to disk for the PDF/text loaders).
#
# ALLOWED_EXTENSIONS: Whitelist > blacklist. If we blacklisted ".exe",
#   an attacker could upload ".bat", ".sh", ".py", etc. A whitelist means
#   only formats we explicitly handle are accepted.
#
# UPLOAD_DIR: Files land in a server-controlled directory with UUID names.
#   The original filename is NEVER used on the filesystem — this prevents
#   path traversal ("../../etc/passwd") and filename collision attacks.
# ─────────────────────────────────────────────────────────────────────────────
MAX_UPLOAD_SIZE = 20 * 1024 * 1024   # 20 MB
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md"}
UPLOAD_DIR = Path(
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
)


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic request schemas
# ─────────────────────────────────────────────────────────────────────────────
class RequestState(BaseModel):
    session_id: Optional[str] = "default"   # for tracking conversation history
    model_name: str
    model_provider: str
    system_prompt: str
    messages: List[str]   # chat history (list of user messages)
    allow_search: bool = False
    retrieved_chunks: Optional[List[dict]] = None
    use_tool_routing: bool = True   # enable/disable the tool router step


class DecideRequest(BaseModel):
    query: str
    model_name: str
    model_provider: str


# ─────────────────────────────────────────────────────────────────────────────
# Allowed models & logging
# ─────────────────────────────────────────────────────────────────────────────
ALLOWED_MODEL_NAMES = [
    "mixtral-8x7b-32768",
    "llama-3.3-70b-versatile",
    "meta-llama/llama-3.1-70b-instruct"
]

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


# ─────────────────────────────────────────────────────────────────────────────
# Application lifespan
#
# WHY lifespan over @app.on_event("startup")?
# on_event is deprecated in modern FastAPI. The lifespan context manager
# is the recommended pattern — it gives you both startup AND shutdown
# hooks in one place, and plays nicely with async.
# ─────────────────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(application: FastAPI):
    # ── Startup ──
    init_db()
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    logging.info("Database initialized, upload directory ready.")
    yield
    # ── Shutdown ──
    logging.info("Application shutting down.")


app = FastAPI(
    title="LangGraph Research & Summarization Agent",
    description=(
        "Backend API for RAG Agent with chat, ingestion, structured summaries, "
        "and an explicit Tool Router that decides which tool to use before execution."
    ),
    version="1.3",
    lifespan=lifespan,
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
    # ── Input validation ──────────────────────────────────────────────────
    # WHY validate here instead of relying on Pydantic?
    # Pydantic validates the *type* (List[str]), but `[]` is a valid list.
    # Indexing into an empty list (`messages[-1]`) raises IndexError,
    # which would surface as a cryptic 500. Explicit validation gives the
    # caller a clear, actionable 400 error message.
    if request.model_name not in ALLOWED_MODEL_NAMES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model name '{request.model_name}'. "
                   f"Allowed: {ALLOWED_MODEL_NAMES}",
        )

    if not request.messages:
        raise HTTPException(
            status_code=400,
            detail="messages list cannot be empty — at least one user message is required.",
        )

    try:
        session_id = request.session_id or "default"

        # Persist incoming user messages to SQLite
        for msg in request.messages:
            save_message(session_id, "user", msg)

        llm_id = request.model_name
        query = request.messages[-1]  # take latest message only
        system_prompt = request.system_prompt
        provider = request.model_provider
        allow_search = request.allow_search

        # Fetch full conversation history from DB for context
        history = get_session_messages_as_list(session_id)
        # Exclude the current query (last item) from history passed to agent
        history = history[:-1] if history else []

        start = time.time()

        # ── Mode 1: Direct RAG from provided chunks ────────────────────────
        if request.retrieved_chunks:
            response = summarize_with_evidence(request.retrieved_chunks)

        # ── Mode 2: Tool-Routed execution (new default) ────────────────────
        elif request.use_tool_routing:
            response = get_response_with_routing(
                llm_id=llm_id,
                query=query,
                system_prompt=system_prompt,
                provider=provider,
                allow_search=allow_search,
                conversation_history=history,
            )

        # ── Mode 3: Legacy ReAct agent (opt-out of routing) ───────────────
        else:
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

        # Persist assistant response to SQLite
        assistant_response = ""
        if "summary" in response and response["summary"]:
            assistant_response = response["summary"][0]
        elif response.get("raw_response"):
            assistant_response = response["raw_response"]

        if assistant_response:
            save_message(session_id, "assistant", assistant_response)

        # Add metadata
        response["latency"] = latency
        response["model_used"] = llm_id
        response["session_id"] = session_id

        return response

    except HTTPException:
        # Re-raise HTTPExceptions so FastAPI handles them correctly
        # (without this, the generic `except Exception` below would swallow them)
        raise
    except Exception as e:
        logging.error(f"Error in chat_endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}",
        )


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
        raise HTTPException(
            status_code=400,
            detail=f"Invalid model name '{request.model_name}'. "
                   f"Allowed: {ALLOWED_MODEL_NAMES}",
        )
    try:
        llm = _build_llm(request.model_provider, request.model_name)
        decision = decide_tool(request.query, llm, conversation_history=[])
        return {
            "query": request.query,
            "tool": decision.tool,
            "input": decision.input,
            "available_tools": list(get_tool_descriptions().keys()),
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error in decide_endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}",
        )


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
def get_history_endpoint(session_id: str, limit: int = 50, offset: int = 0):
    """
    Fetch paginated message history for a given session.

    WHY pagination?
    ────────────────
    Without it, a session with 10,000 messages returns them ALL in one
    JSON response. That's slow to serialize, slow to transmit, and the
    frontend probably can't render it all at once anyway. Pagination keeps
    response sizes predictable and lets the frontend load on demand.

    Query params:
      - limit:  max messages per page (default 50)
      - offset: skip this many messages (default 0)
    """
    if limit < 1 or limit > 200:
        raise HTTPException(
            status_code=400,
            detail="limit must be between 1 and 200.",
        )
    if offset < 0:
        raise HTTPException(
            status_code=400,
            detail="offset must be non-negative.",
        )

    messages, total = get_history(session_id, limit=limit, offset=offset)
    return {
        "session_id": session_id,
        "history": messages,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


# ── /models ───────────────────────────────────────────────────────────────────
@app.get("/models", summary="List available models")
def list_models():
    """Get the list of models supported by this backend"""
    return {"available_models": ALLOWED_MODEL_NAMES}


# ── /health ───────────────────────────────────────────────────────────────────
@app.get("/health", summary="Health check")
def health_check():
    """Verify that the API is running"""
    return {"status": "ok", "service": "RAG Agent Backend v1.3", "tool_routing": "enabled"}


# ── /ingest ───────────────────────────────────────────────────────────────────
@app.post("/ingest", summary="Ingest document into vector store")
async def ingest_document_endpoint(file: UploadFile = File(...)):
    """
    Upload and ingest a PDF, TXT, or MD file into the FAISS vector database.

    WHY UploadFile instead of a file_path string?
    ──────────────────────────────────────────────
    Accepting a raw path from the client is a **path traversal vulnerability**.
    The client could send "../../etc/passwd" and force the server to read any
    file on disk. UploadFile receives the actual file bytes — the server
    controls where they land on the filesystem.

    Security measures applied:
    1. Extension whitelist (.pdf, .txt, .md) — not a blacklist.
    2. UUID-based filename — the original name is never used on disk.
    3. Size cap (20 MB) — prevents denial-of-service via huge uploads.
    4. Cleanup — the temp file is removed after ingestion succeeds.

    WHY async?
    ──────────
    UploadFile.read() is an async operation. Making this endpoint async
    lets FastAPI use the event loop efficiently instead of blocking a
    thread pool worker while reading bytes.
    """
    from backend.tools.retriever import ingest_document

    # ── 1. Validate extension ─────────────────────────────────────────────
    # We extract from the *original* filename for user-friendliness
    # (so ".PDF" works too), but never trust it for the saved path.
    original_name = file.filename or ""
    ext = Path(original_name).suffix.lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Allowed: {sorted(ALLOWED_EXTENSIONS)}",
        )

    # ── 2. Read & validate size ───────────────────────────────────────────
    # WHY read into memory first?
    # We need the full bytes to check size AND to write to disk.
    # For files up to 20 MB this is fine. For truly large files (100+ MB)
    # you'd stream to disk in chunks and check size incrementally.
    contents = await file.read()

    if len(contents) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({len(contents)} bytes). "
                   f"Maximum allowed: {MAX_UPLOAD_SIZE} bytes ({MAX_UPLOAD_SIZE // (1024*1024)} MB).",
        )

    if len(contents) == 0:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty.",
        )

    # ── 3. Save with UUID filename ────────────────────────────────────────
    safe_name = f"{uuid4()}{ext}"
    save_path = UPLOAD_DIR / safe_name

    try:
        save_path.write_bytes(contents)

        # ── 4. Ingest into vector store ───────────────────────────────────
        result = ingest_document(str(save_path))

        return {
            "status": "success",
            "original_filename": original_name,
            "stored_as": safe_name,
            "size_bytes": len(contents),
            **result,
        }

    except ValueError as e:
        # ValueError from retriever (e.g., unsupported file type)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"Error ingesting document: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to ingest document: {str(e)}",
        )
    finally:
        # Clean up the uploaded file after ingestion
        # (the content is now in the FAISS index)
        if save_path.exists():
            try:
                save_path.unlink()
            except OSError:
                logging.warning(f"Could not remove temp file: {save_path}")


# Step 3: Run app & Explore Swagger UI Docs
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=9999)
