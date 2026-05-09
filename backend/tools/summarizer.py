# backend/tools/summarizer.py

import json
import os
from typing import List, Dict, Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError
from openai import OpenAI
from backend.config import LLM_MODEL

load_dotenv()

# Initialize OpenAI client pointed at OpenRouter
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPEN_ROUTER_API_KEY")
)


# ----------------------
# Pydantic schemas
# ----------------------
class ActionItem(BaseModel):
    assignee: Optional[str] = None
    task: str
    deadline: Optional[str] = None


class ProsCons(BaseModel):
    pros: List[str] = []
    cons: List[str] = []


class SummaryOutput(BaseModel):
    summary: List[str] = Field(..., description="Concise bullet points")
    pros_cons: Optional[ProsCons] = None
    action_items: List[ActionItem] = []
    citations: List[str] = []
    raw: Optional[str] = None   # keep raw text as fallback / debugging


# ----------------------
# Helper: schema example
# ----------------------
PROMPT_SCHEMA_EXAMPLE = {
    "summary": ["short bullet 1", "short bullet 2"],
    "pros_cons": {"pros": ["pro1"], "cons": ["con1"]},
    "action_items": [{"assignee": "Alice", "task": "Prepare slide deck", "deadline": "2025-09-20"}],
    "citations": ["paper.pdf#chunk:3"]
}


# ----------------------
# Helper: build prompt
# ----------------------
def _build_prompt(retrieved_chunks: List[dict]) -> str:
    """
    Build the prompt text to give the LLM.
    retrieved_chunks: list of dicts with keys: source_id, chunk_id, text, score
    """
    context_parts = []
    for c in retrieved_chunks:
        tag = f"[source:{c.get('source_id')}#chunk:{c.get('chunk_id')}]"
        context_parts.append(f"{tag}\n{c.get('text')}\n")
    context = "\n---\n".join(context_parts)

    prompt = f"""
You are a research assistant. Given the context excerpts below, produce a JSON object ONLY
(no extra explanation, no surrounding text).
The JSON must follow this schema exactly:

- summary: array of short bullet strings (concise takeaways).
- pros_cons: object with two arrays: pros and cons (optional, include if relevant).
- action_items: list of objects with keys: assignee (or null), task (string), deadline (string or null).
- citations: list of citation tags used in findings (e.g., "paper.pdf#chunk:3").

Return only a single valid JSON object. DO NOT include any markdown or commentary.

Example of the JSON format:
{json.dumps(PROMPT_SCHEMA_EXAMPLE, indent=2)}

Context excerpts:
{context}

Now produce the JSON.
"""
    return prompt


# ----------------------
# Helper: attempt repair
# ----------------------
def _attempt_repair(raw_text: str) -> Optional[dict]:
    """
    If the model returns invalid JSON, try repairing it.
    """
    repair_prompt = (
        "The assistant returned text that is not valid JSON. "
        "Extract and return ONLY the valid JSON object that matches the schema described:\n\n"
        "Schema:\n"
        "- summary: list of short bullets\n"
        "- pros_cons: {'pros': [...], 'cons': [...]}, optional\n"
        "- action_items: list of {'assignee', 'task', 'deadline'}\n"
        "- citations: list of citation strings\n\n"
        f"Here is the original (possibly invalid) output:\n\"\"\"{raw_text}\"\"\"\n\n"
        "Please return only the JSON object (no explanation)."
    )
    resp = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": repair_prompt}],
        temperature=0.0,
        max_tokens=800
    )
    candidate = resp.choices[0].message.content
    try:
        return json.loads(candidate)
    except Exception:
        return None


# ----------------------
# Main summarizer function
# ----------------------
def summarize_with_evidence(retrieved_chunks: List[dict]) -> Dict:
    """
    retrieved_chunks: list of {source_id, chunk_id, text, score}
    Returns structured JSON dict matching SummaryOutput schema.
    """
    prompt = _build_prompt(retrieved_chunks)

    # Call the model
    resp = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=1200
    )
    content = resp.choices[0].message.content

    # Try direct parse
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        repaired = _attempt_repair(content)
        parsed = repaired if repaired is not None else {"raw": content}

    # Validate with Pydantic
    try:
        validated = SummaryOutput.model_validate(parsed)
        return validated.model_dump()
    except ValidationError as e:
        return {"raw": content, "validation_error": str(e)}
