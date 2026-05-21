# backend/tool_router.py
"""
Tool Router: A dedicated LLM step that decides whether a tool should be
used to answer a user query, and if yes, which tool and with what input.

The router uses a structured system prompt that forces the LLM to output
strict JSON: {"tool": "<name | no_tool>", "input": "<clean query>"}
"""

import json
import logging

from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)


# ── Tool Registry ──────────────────────────────────────────────────────────────
TOOL_DESCRIPTIONS = {
    "research_tool": {
        "name": "research_tool",
        "description": (
            "Retrieve and summarize information from ingested/uploaded documents "
            "stored in the local knowledge base (vector store). Use this when the "
            "user asks about content from PDFs, text files, or documents that have "
            "been ingested. Returns structured notes with citations."
        ),
        "input_format": "A concise search query describing what information to retrieve from stored documents.",
    },
    "web_search": {
        "name": "web_search",
        "description": (
            "Search the live internet (via Tavily) for current, real-time, or "
            "up-to-date information. Use this when the question requires news, "
            "current events, recent data, or anything not likely stored in the "
            "local knowledge base."
        ),
        "input_format": "A focused web search query (keywords only, no filler words).",
    },
    "no_tool": {
        "name": "no_tool",
        "description": (
            "No external tool is needed. Use this for general knowledge questions, "
            "conversational messages, greetings, or simple factual questions the "
            "LLM can answer directly from its training data."
        ),
        "input_format": "N/A",
    },
}


def _format_tool_descriptions() -> str:
    """Format tool registry into a prompt-friendly multi-line string."""
    lines = []
    for info in TOOL_DESCRIPTIONS.values():
        lines.append(
            f"Tool: {info['name']}\n"
            f"  Description: {info['description']}\n"
            f"  Input Format: {info['input_format']}"
        )
    return "\n\n".join(lines)


# ── System Prompt (parameterised with tool descriptions) ───────────────────────
TOOL_ROUTER_SYSTEM_PROMPT = """You are a precise AI agent whose ONLY job is to decide whether a tool should be used to
answer a user query, and if yes, which tool and with what input.

You must NOT answer the user's question.

---

AVAILABLE TOOLS:
{tool_descriptions}

Each tool has:
- a name
- a description of what it does
- the expected input format

---

YOUR TASK:

1. Read the user query carefully.
2. Read the CHAT HISTORY to understand the context of the current query.
3. Resolve any ambiguous references (e.g., "it", "that", "the document", "more info") using the history.
4. Decide:
   - If a tool is needed → choose the BEST matching tool
   - If no tool is needed → choose "no_tool"

5. If a tool is selected:
   - The "input" MUST be the RESOLVED version of the query (e.g., if user says "Tell me more about it" and
     "it" is LangGraph, input should be "LangGraph").
   - Clean the input (remove unnecessary words).
   - Keep it precise and usable.

---

SELECTION RULES:

- Choose ONLY from the available tools.
- Do NOT invent new tools.
- **Reference Resolution**: If the query contains pronouns (it, that, they) or vague terms (the topic, more info),
  you MUST resolve them using the CHAT HISTORY before deciding.
- **Topic Persistence**: If the resolved topic was previously handled by `research_tool` or `web_search`,
  continue using that tool unless the user explicitly asks to switch.
- If the query directly asks to analyze, summarize, translate, or extract → use a tool.
- If the query is general knowledge, a greeting, or simple conversation → use "no_tool".
- **Crucial**: If the resolved query is "Tell me more about LangChain", this is NOT "general conversation".
  It is a request for more information on a specific topic, so use the relevant tool (`research_tool` or `web_search`).

---

OUTPUT FORMAT (STRICT — NO EXTRA TEXT):

{{
  "tool": "<tool_name OR no_tool>",
  "input": "<resolved and clean input>"
}}

---

CHAT HISTORY (for reference resolution):
{chat_history}"""


# ── Pydantic Schema for the Decision ──────────────────────────────────────────
class ToolDecision(BaseModel):
    tool: str
    input: str


# ── Core Decision Function ─────────────────────────────────────────────────────
def decide_tool(query: str, llm, conversation_history: list = None) -> ToolDecision:
    """
    Ask the LLM (acting as a router) to decide which tool to use for a query.

    Args:
        query: The raw user query string.
        llm:   A LangChain chat model instance (ChatGroq or ChatOpenAI).
        conversation_history: List of previous user messages.

    Returns:
        ToolDecision with 'tool' and 'input' fields.
        Falls back to no_tool on any error.
    """
    from langchain_core.messages import HumanMessage, SystemMessage

    # Format chat history for the router
    if conversation_history:
        history_str = "\n".join([f"User: {msg}" for msg in conversation_history])
    else:
        history_str = "No previous conversation."

    tool_descriptions_str = _format_tool_descriptions()
    system_content = TOOL_ROUTER_SYSTEM_PROMPT.format(
        tool_descriptions=tool_descriptions_str,
        chat_history=history_str
    )

    messages = [
        SystemMessage(content=system_content),
        HumanMessage(content=query),
    ]

    try:
        response = llm.invoke(messages)
        raw = response.content.strip()

        # Strip markdown code fences if model wraps output in them
        if raw.startswith("```"):
            parts = raw.split("```")
            raw = parts[1] if len(parts) > 1 else raw
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        parsed = json.loads(raw)

        # Guard: only accept known tool names
        if parsed.get("tool") not in TOOL_DESCRIPTIONS:
            logger.warning(
                f"[ToolRouter] Unknown tool '{parsed.get('tool')}' returned. "
                "Defaulting to no_tool."
            )
            parsed["tool"] = "no_tool"
            parsed["input"] = query

        decision = ToolDecision(**parsed)
        logger.info(
            f"[ToolRouter] Decision → tool={decision.tool!r}, input={decision.input!r}"
        )
        return decision

    except (json.JSONDecodeError, ValidationError, Exception) as exc:
        logger.error(f"[ToolRouter] Error parsing decision: {exc}. Falling back to no_tool.")
        return ToolDecision(tool="no_tool", input=query)


# ── Utility: Describe available tools (for API exposure) ──────────────────────
def get_tool_descriptions() -> dict:
    """Return the full tool registry (used by the /tools endpoint)."""
    return TOOL_DESCRIPTIONS
