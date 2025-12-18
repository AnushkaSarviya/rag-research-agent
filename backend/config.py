# backend/config.py

import os

# Default model for summarizer (OpenRouter)
LLM_MODEL = os.getenv(
    "OPEN_ROUTER_SUMMARY_MODEL",
    "meta-llama/llama-3.1-70b-instruct"  # fallback model
)

VECTOR_DB_PATH = "vector_store"
