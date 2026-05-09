# backend/main.py

# Step 1: Setup Pydantic Model (Schema Validation)
import time
import logging
from pydantic import BaseModel
from typing import List, Optional
from fastapi import FastAPI
from backend.ai_agent import get_response_from_ai_agent
from backend.tools.summarizer import summarize_with_evidence


class RequestState(BaseModel):
    session_id: Optional[str] = "default"   # for tracking conversation history
    model_name: str
    model_provider: str
    system_prompt: str
    messages: List[str]   # chat history (list of user messages)
    allow_search: bool = False
    retrieved_chunks: Optional[List[dict]] = None


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
    description="Backend API for RAG Agent with chat, ingestion, and structured summaries.",
    version="1.1"
)


@app.post(
    "/chat",
    summary="Chat with the Research & Summarization Agent",
    description="Send user messages and get structured research summaries with citations.",
    response_description="Structured summary from the agent"
)
def chat_endpoint(request: RequestState):
    """
    API Endpoint to interact with the Research & Summarization Agent.
    If 'retrieved_chunks' are provided, use RAG summarizer instead of plain chatbot.
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

        # ---- If retrieved chunks are passed, run RAG summarizer ----
        if request.retrieved_chunks:
            response = summarize_with_evidence(request.retrieved_chunks)
        else:
            # Otherwise fall back to plain chatbot with optional web search
            history = conversation_history.get(session_id, [])[:-1]  # All but current message
            plain_response = get_response_from_ai_agent(
                llm_id,
                query,
                system_prompt,
                provider,
                allow_search=allow_search,
                conversation_history=history
            )
            response = {
                "summary": [plain_response],
                "pros_cons": {"pros": [], "cons": []},
                "action_items": [],
                "citations": []
            }

        latency = round(time.time() - start, 2)
        logging.info(f"[Session={session_id}] Model={llm_id}, Latency={latency}s, Query={query}")

        # Add metadata
        response["latency"] = latency
        response["model_used"] = llm_id
        response["session_id"] = session_id

        return response

    except Exception as e:
        logging.error(f"Error in chat_endpoint: {e}", exc_info=True)
        return {"error": f"Backend error: {str(e)}"}


@app.get("/history/{session_id}", summary="Get chat history by session ID")
def get_history(session_id: str):
    """Fetch all past messages for a given session"""
    return {"session_id": session_id, "history": conversation_history.get(session_id, [])}


@app.get("/models", summary="List available models")
def list_models():
    """Get the list of models supported by this backend"""
    return {"available_models": ALLOWED_MODEL_NAMES}


@app.get("/health", summary="Health check")
def health_check():
    """Verify that the API is running"""
    return {"status": "ok", "service": "RAG Agent Backend"}


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
