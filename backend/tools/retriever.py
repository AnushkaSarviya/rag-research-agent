# backend/tools/retriever.py

import os
from typing import List
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

VECTOR_DB_PATH = "vector_store"

# Embeddings using OpenRouter (OpenAI compatible)
embeddings = OpenAIEmbeddings(
    model="text-embedding-3-small",
    api_key=os.getenv("OPEN_ROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

# -----------------------------
# 1. Load & Chunk Documents
# -----------------------------
def ingest_document(file_path: str):
    """Load a PDF or text file, split into chunks, and store in FAISS DB."""
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    ext = file_path.lower()
    if ext.endswith(".pdf"):
        loader = PyPDFLoader(file_path)
    elif ext.endswith((".txt", ".text", ".md")):
        loader = TextLoader(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_path}. Supported: .pdf, .txt, .text, .md")

    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=400,
        chunk_overlap=80
    )
    chunks = splitter.split_documents(docs)

    if os.path.exists(VECTOR_DB_PATH):
        db = FAISS.load_local(VECTOR_DB_PATH, embeddings, allow_dangerous_deserialization=True)
        db.add_documents(chunks)
    else:
        db = FAISS.from_documents(chunks, embeddings)

    db.save_local(VECTOR_DB_PATH)

    return {"status": "success", "chunks_added": len(chunks)}


# -----------------------------
# 2. Retrieve Chunks
# -----------------------------
def retrieve(query: str, top_k: int = 5) -> List[dict]:
    """Retrieve relevant chunks for a given query."""

    if not os.path.exists(VECTOR_DB_PATH):
        return []

    db = FAISS.load_local(VECTOR_DB_PATH, embeddings, allow_dangerous_deserialization=True)
    results = db.similarity_search_with_score(query, k=top_k)

    retrieved_chunks = []
    for i, (doc, score) in enumerate(results):
        retrieved_chunks.append({
            "source_id": doc.metadata.get("source", "unknown_doc"),
            "chunk_id": i,
            "text": doc.page_content,
            "score": float(score)
        })

    return retrieved_chunks
