# ───────────── IMPORTS ───────────────────────────────────────────────────────
# FIX #1: Removed the auto-pip-install block (dependencies managed via requirements.txt).
import os
import uuid
from datetime import date

import requests
import streamlit as st
from streamlit_lottie import st_lottie  # noqa: F401


# ───────────── API CONFIG ────────────────────────────────────────────────────
# FIX #2: Environment variable with safe fallback for Docker / local development.
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:9999")


# ───────────── PAGE CONFIG ───────────────────────────────────────────────────
st.set_page_config(
    page_title="Agentic Studio",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ───────────── HELPER ────────────────────────────────────────────────────────
def load_lottieurl(url: str):
    try:
        r = requests.get(url, timeout=5)
        if r.status_code != 200:
            return None
        return r.json()
    except Exception:
        return None


lottie_ai = load_lottieurl(
    "https://assets3.lottiefiles.com/packages/lf20_dbbxfnjo.json"
)


# ───────────── CUSTOM CSS (DARK FUTURISTIC GLASSMORPHISM THEME) ─────────────
custom_css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Reset & Global Typography ────────────────── */
html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    color: #e2e8f0;
}

/* ── Background Gradients & Ambient Glow ──────── */
.stApp {
    background: radial-gradient(circle at 15% 15%, rgba(139, 92, 246, 0.15) 0%, transparent 40%),
                radial-gradient(circle at 85% 85%, rgba(0, 229, 255, 0.12) 0%, transparent 40%),
                radial-gradient(circle at 50% 50%, rgba(236, 72, 153, 0.06) 0%, transparent 60%),
                #080C14 !important;
    background-attachment: fixed !important;
}

/* Main Container Layout */
.block-container {
    padding-top: 2rem !important;
    padding-bottom: 6rem !important;
    max-width: 52rem !important;
}

/* ── Typography & Headers ─────────────────────── */
.header-container {
    margin-bottom: 2rem;
}

.main-header-title {
    background: linear-gradient(135deg, #00E5FF 0%, #8B5CF6 50%, #EC4899 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2.5rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    margin: 0;
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.main-header-subtitle {
    color: #94a3b8;
    font-size: 0.95rem;
    font-weight: 500;
    margin-top: 0.3rem;
}

/* ── Sidebar Glassmorphism ────────────────────── */
[data-testid="stSidebar"] {
    background: rgba(13, 17, 29, 0.85) !important;
    backdrop-filter: blur(24px) !important;
    -webkit-backdrop-filter: blur(24px) !important;
    border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
}

[data-testid="stSidebar"] * {
    color: #cbd5e1 !important;
}

.sidebar-brand {
    padding: 0.5rem 0 1.25rem 0;
}

.sidebar-brand-title {
    background: linear-gradient(135deg, #00E5FF, #8B5CF6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 1.35rem;
    font-weight: 700;
    margin: 0;
}

.sidebar-brand-subtitle {
    font-size: 0.78rem;
    color: #64748b;
    margin-top: 0.2rem;
    font-weight: 500;
}

/* ── Sidebar Cards & Containers ───────────────── */
.sidebar-section-title {
    font-size: 0.75rem !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #00E5FF !important;
    margin-bottom: 0.75rem;
    display: flex;
    align-items: center;
    gap: 0.4rem;
}

/* ── Chat Message Cards ───────────────────────── */
.stChatMessage {
    background: rgba(15, 23, 42, 0.65) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 16px !important;
    padding: 1.25rem !important;
    margin-bottom: 1.25rem !important;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3) !important;
    backdrop-filter: blur(16px) !important;
    -webkit-backdrop-filter: blur(16px) !important;
    animation: fadeInSlide 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    transition: border-color 0.25s ease, box-shadow 0.25s ease;
}

.stChatMessage:hover {
    border-color: rgba(0, 229, 255, 0.25) !important;
    box-shadow: 0 12px 36px rgba(0, 229, 255, 0.08) !important;
}

@keyframes fadeInSlide {
    from {
        opacity: 0;
        transform: translateY(12px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

/* ── Tool Badges ──────────────────────────────── */
.tool-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.35rem 0.85rem;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
    letter-spacing: 0.02em;
    backdrop-filter: blur(8px);
}
.tool-badge-research {
    background: rgba(0, 229, 255, 0.12);
    color: #00E5FF;
    border: 1px solid rgba(0, 229, 255, 0.35);
    box-shadow: 0 0 14px rgba(0, 229, 255, 0.25);
}
.tool-badge-web {
    background: rgba(236, 72, 153, 0.12);
    color: #EC4899;
    border: 1px solid rgba(236, 72, 153, 0.35);
    box-shadow: 0 0 14px rgba(236, 72, 153, 0.25);
}
.tool-badge-notool {
    background: rgba(139, 92, 246, 0.12);
    color: #A78BFA;
    border: 1px solid rgba(139, 92, 246, 0.35);
    box-shadow: 0 0 14px rgba(139, 92, 246, 0.25);
}
.tool-input-hint {
    font-size: 0.78rem;
    color: #94a3b8;
    margin-bottom: 0.85rem;
    font-family: 'JetBrains Mono', monospace;
}

/* ── Buttons (Gradient & Micro-interactions) ── */
.stButton > button {
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.25), rgba(0, 229, 255, 0.25)) !important;
    color: #f8fafc !important;
    border: 1px solid rgba(0, 229, 255, 0.3) !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    letter-spacing: 0.01em !important;
    padding: 0.55rem 1rem !important;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.2) !important;
}

.stButton > button:hover {
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.45), rgba(0, 229, 255, 0.45)) !important;
    border-color: #00E5FF !important;
    box-shadow: 0 0 22px rgba(0, 229, 255, 0.4) !important;
    transform: translateY(-2px) !important;
}

.stButton > button:active {
    transform: translateY(0) !important;
}

/* Download button */
div[data-testid="stDownloadButton"] > button {
    background: linear-gradient(135deg, rgba(6, 182, 212, 0.25), rgba(139, 92, 246, 0.25)) !important;
    border: 1px solid rgba(6, 182, 212, 0.4) !important;
    border-radius: 10px !important;
    color: #f8fafc !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    transition: all 0.25s ease !important;
}

div[data-testid="stDownloadButton"] > button:hover {
    border-color: #00E5FF !important;
    box-shadow: 0 0 22px rgba(0, 229, 255, 0.4) !important;
    transform: translateY(-2px) !important;
}

/* ── Expanders ────────────────────────────────── */
div[data-testid="stExpander"] {
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 12px !important;
    background: rgba(15, 23, 42, 0.4) !important;
    backdrop-filter: blur(12px) !important;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2) !important;
    margin-bottom: 0.75rem !important;
}

div[data-testid="stExpander"] summary {
    font-weight: 600 !important;
    color: #cbd5e1 !important;
    transition: color 0.2s ease !important;
}

div[data-testid="stExpander"] summary:hover {
    color: #00E5FF !important;
}

/* ── Chat Input ───────────────────────────────── */
.stChatInput>div {
    border-radius: 16px !important;
    border: 1px solid rgba(0, 229, 255, 0.3) !important;
    background: rgba(15, 23, 42, 0.85) !important;
    backdrop-filter: blur(20px) !important;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4) !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

.stChatInput>div:focus-within {
    border-color: #00E5FF !important;
    box-shadow: 0 0 30px rgba(0, 229, 255, 0.4) !important;
}

/* ── File Uploader ────────────────────────────── */
div[data-testid="stFileUploader"] {
    border: 2px dashed rgba(0, 229, 255, 0.35) !important;
    border-radius: 14px !important;
    background: rgba(15, 23, 42, 0.4) !important;
    padding: 1rem !important;
    transition: all 0.3s ease !important;
}

div[data-testid="stFileUploader"]:hover {
    border-color: #00E5FF !important;
    box-shadow: 0 0 24px rgba(0, 229, 255, 0.25) !important;
    background: rgba(15, 23, 42, 0.65) !important;
}

/* ── Form Inputs & Selects ────────────────────── */
div[data-baseweb="select"] > div {
    background-color: rgba(15, 23, 42, 0.8) !important;
    border-color: rgba(255, 255, 255, 0.12) !important;
    border-radius: 10px !important;
}

div[data-baseweb="select"] > div:hover {
    border-color: #00E5FF !important;
}

/* ── Status Widget ────────────────────────────── */
div[data-testid="stStatusWidget"] {
    border-radius: 12px !important;
    border: 1px solid rgba(139, 92, 246, 0.35) !important;
    background: rgba(15, 23, 42, 0.75) !important;
}

/* ── Hero Starter Cards ───────────────────────── */
.hero-card {
    background: rgba(15, 23, 42, 0.55);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    padding: 1.25rem;
    transition: all 0.3s ease;
    backdrop-filter: blur(12px);
    height: 100%;
}

.hero-card:hover {
    border-color: rgba(0, 229, 255, 0.4);
    transform: translateY(-3px);
    box-shadow: 0 10px 30px rgba(0, 229, 255, 0.15);
}

.hero-card-icon {
    font-size: 1.5rem;
    margin-bottom: 0.5rem;
}

.hero-card-title {
    font-weight: 700;
    color: #f1f5f9;
    font-size: 1rem;
    margin-bottom: 0.3rem;
}

.hero-card-desc {
    color: #94a3b8;
    font-size: 0.83rem;
    line-height: 1.4;
}

/* ── Top Status Pills ─────────────────────────── */
.status-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.3rem 0.75rem;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 600;
    background: rgba(15, 23, 42, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.08);
    color: #cbd5e1;
}

.status-pill-active {
    border-color: rgba(0, 229, 255, 0.4);
    color: #00E5FF;
}

/* Hide Streamlit default chrome */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)


# ───────────── TOOL BADGE HELPER ─────────────────────────────────────────────
TOOL_ICONS = {
    "research_tool": ("›", "tool-badge-research", "RAG · Knowledge Base"),
    "web_search":    ("»", "tool-badge-web",      "Web Search · Tavily"),
    "no_tool":       ("·", "tool-badge-notool",   "Direct LLM · No Tool"),
}


def render_tool_badge(tool_decision: dict):
    tool = tool_decision.get("tool", "no_tool")
    tool_input = tool_decision.get("input", "")
    icon, css_class, label = TOOL_ICONS.get(tool, ("▪", "tool-badge-notool", tool))

    st.markdown(
        f"""
        <div class="tool-badge {css_class}">
            {icon}&nbsp; Tool Router → <strong>{label}</strong>
        </div>
        <div class="tool-input-hint">&gt; Extracted input: <em>"{tool_input}"</em></div>
        """,
        unsafe_allow_html=True,
    )


# ───────────── RESPONSE RENDERER ─────────────────────────────────────────────
def render_response(data: dict):
    if "tool_decision" in data:
        render_tool_badge(data["tool_decision"])

    if "summary" in data and data["summary"]:
        st.markdown("### ≡ Summary")
        for item in data["summary"]:
            st.markdown(f"- {item}")

    if "pros_cons" in data and (
        data["pros_cons"].get("pros") or data["pros_cons"].get("cons")
    ):
        with st.expander("⚖️ Pros & Cons", expanded=True):
            c1, c2 = st.columns(2)
            with c1:
                if data["pros_cons"].get("pros"):
                    st.markdown("#### ✓ Pros")
                    for pro in data["pros_cons"]["pros"]:
                        st.markdown(f"- {pro}")
            with c2:
                if data["pros_cons"].get("cons"):
                    st.markdown("#### ✕ Cons")
                    for con in data["pros_cons"]["cons"]:
                        st.markdown(f"- {con}")

    if "action_items" in data and data["action_items"]:
        with st.expander("📋 Action Items", expanded=True):
            for item in data["action_items"]:
                assignee = item.get("assignee", "Unassigned")
                task = item.get("task", "")
                deadline = item.get("deadline", "No deadline")
                st.markdown(f"- **{task}** (Assignee: {assignee}, Deadline: {deadline})")

    if "citations" in data and data["citations"]:
        with st.expander("📚 Citations", expanded=False):
            for citation in data["citations"]:
                st.markdown(f"- `{citation}`")

    # Latency + Model metadata caption
    if "latency" in data:
        st.caption(
            f"~ {data['latency']}s | "
            f"Model: {data.get('model_used', 'N/A')} | "
            f"Session: {data.get('session_id', 'N/A')}"
        )


# ───────────── STATE INIT ────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "ingested_files" not in st.session_state:
    st.session_state.ingested_files = []


# ───────────── EXPORT HELPER ─────────────────────────────────────────────────
def build_chat_export() -> str:
    """Formats conversation as Markdown for export."""
    today = date.today().isoformat()
    lines = [f"## Chat Export — {st.session_state.session_id} — {today}", ""]
    for msg in st.session_state.messages:
        role = msg["role"]
        content = msg["content"]
        if role == "user":
            lines.append(f"**User:** {content}")
        else:
            summary = content.get("summary") if isinstance(content, dict) else None
            if summary:
                lines.append("**Assistant:**")
                for item in summary:
                    lines.append(f"- {item}")
            else:
                lines.append(f"**Assistant:** {content}")
        lines.append("")
    return "\n".join(lines)


# ───────────── SIDEBAR CONFIG ────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-brand">
            <h2 class="sidebar-brand-title">◆ Agentic Studio</h2>
            <div class="sidebar-brand-subtitle">Production RAG & Autonomous Agent</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<div class='sidebar-section-title'>📡 Model Configuration</div>", unsafe_allow_html=True)
    provider = st.radio("Provider", ("Groq", "OpenRouter"), horizontal=True, label_visibility="collapsed")
    MODEL_NAMES_GROQ = ["llama-3.3-70b-versatile", "mixtral-8x7b-32768"]
    MODEL_NAMES_OPENROUTER = ["meta-llama/llama-3.1-70b-instruct"]
    selected_model = st.selectbox(
        "Model",
        MODEL_NAMES_GROQ if provider == "Groq" else MODEL_NAMES_OPENROUTER,
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("<div class='sidebar-section-title'>⚡ Engine Capabilities</div>", unsafe_allow_html=True)
    allow_web_search = st.toggle("Enable Web Search (Tavily)", value=True)
    use_tool_routing = st.toggle("Enable Smart Routing", value=True)

    ADVANCED_PROMPT = """You are an AI assistant that answers user queries using:

1. Current query
2. Short-term memory (recent conversation)
3. Long-term memory (retrieved user data)

---

INPUTS:

USER QUERY:
{query}

SHORT-TERM MEMORY:
{chat_history}

LONG-TERM MEMORY:
{long_term_memory}

---

YOUR TASK:

1. Understand the query.
2. Use short-term memory to:
   - maintain conversation flow
   - resolve references (e.g., "it", "that")

3. Use long-term memory to:
   - personalize the response
   - recall relevant past preferences or topics

---

RULES:

- Use memory ONLY if relevant
- Do NOT assume missing information
- Do NOT repeat unnecessary past details
- Do NOT mention memory sources

---

BEHAVIOR:

- If memory is relevant → use it naturally
- If not → ignore it completely

---

OUTPUT:

Provide a clear, concise, context-aware answer.

DO NOT include:
- reasoning steps
- system explanations
- references to memory"""
    SYSTEM_PROMPT = ADVANCED_PROMPT

    st.markdown("---")

    # ── RAG / Ingest section ──────────────────────────────────────────────────
    with st.expander("📁 Add Context (RAG)", expanded=False):
        if not st.session_state.ingested_files:
            st.info("No documents ingested yet. Upload a PDF, TXT, or MD file below.")
        else:
            for entry in st.session_state.ingested_files:
                st.success(
                    f"✓ **{entry['filename']}**\n"
                    f"ID: `{entry['file_id'][:8]}…` | {entry['chunks_added']} chunks"
                )

        uploaded_file = st.file_uploader(
            "Upload reference document",
            type=["pdf", "txt", "md"],
            help="Upload a PDF, TXT, or MD file to add to the RAG knowledge base.",
            label_visibility="collapsed",
        )
        if uploaded_file is not None:
            os.makedirs("scratch", exist_ok=True)
            temp_path = os.path.abspath(os.path.join("scratch", uploaded_file.name))
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            if st.button("Ingest Document", use_container_width=True):
                with st.spinner("Ingesting into vector store..."):
                    try:
                        ingest_url = f"{API_BASE_URL}/ingest"
                        with open(temp_path, "rb") as f:
                            files = {"file": (uploaded_file.name, f, "application/octet-stream")}
                            resp = requests.post(ingest_url, files=files, timeout=60)
                        if resp.status_code == 200:
                            res_data = resp.json()
                            if res_data.get("status") == "success":
                                st.session_state.ingested_files.append({
                                    "filename": uploaded_file.name,
                                    "file_id": res_data.get("file_id", "N/A"),
                                    "chunks_added": res_data.get("chunks_added", 0),
                                })
                                st.rerun()
                            else:
                                st.error(f"Ingestion failed: {res_data.get('message')}")
                        else:
                            st.error(f"Error {resp.status_code}: {resp.text}")
                    except Exception as e:
                        st.error(f"Connection error: {e}")

    st.markdown("---")

    # Clear Chat History Button
    if st.button("✕ Clear Chat History", use_container_width=True):
        try:
            delete_url = f"{API_BASE_URL}/history/{st.session_state.session_id}"
            r = requests.delete(delete_url, timeout=10)
            if r.status_code not in (200, 204, 404):
                st.warning(f"Backend clear returned {r.status_code}. Local chat cleared.")
        except Exception:
            st.warning("Could not reach backend to clear server-side history. Local chat cleared.")
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()

    st.markdown("---")

    # Export Chat (.md)
    export_data = build_chat_export()
    st.download_button(
        label="⬇ Export Chat (.md)",
        data=export_data,
        file_name=f"chat_{st.session_state.session_id[:8]}_{date.today().isoformat()}.md",
        mime="text/markdown",
        use_container_width=True,
        disabled=len(st.session_state.messages) == 0,
    )

    st.caption(f"Session: `{st.session_state.session_id[:8]}…`")


# ───────────── MAIN LAYOUT & HEADER ──────────────────────────────────────────
# Top Header Banner
st.markdown(
    """
    <div class="header-container">
        <h1 class="main-header-title">◆ Agentic Studio</h1>
        <div class="main-header-subtitle">Production-Grade Autonomous RAG & Multi-Tool Intelligence</div>
    </div>
    """,
    unsafe_allow_html=True
)

# Status Pill Bar
c1, c2, c3 = st.columns([4, 4, 4])
with c1:
    st.markdown(f"<div class='status-pill status-pill-active'>📡 Model: <strong>{selected_model}</strong></div>", unsafe_allow_html=True)
with c2:
    st.markdown(f"<div class='status-pill status-pill-active'>⚡ Routing: <strong>{'ON' if use_tool_routing else 'OFF'}</strong></div>", unsafe_allow_html=True)
with c3:
    st.markdown(f"<div class='status-pill'>🌐 Search: <strong>{'Enabled' if allow_web_search else 'Disabled'}</strong></div>", unsafe_allow_html=True)

st.markdown("---")

# ───────────── HERO WELCOME (EMPTY CHAT STATE) ────────────────────────────────
if len(st.session_state.messages) == 0:
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.markdown(
            """
            <div class="hero-card">
                <div class="hero-card-icon">⚡</div>
                <div class="hero-card-title">Smart Tool Routing</div>
                <div class="hero-card-desc">Automatically routes your query between RAG vector search, live web search, or direct LLM execution.</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col_b:
        st.markdown(
            """
            <div class="hero-card">
                <div class="hero-card-icon">📚</div>
                <div class="hero-card-title">RAG Context Engine</div>
                <div class="hero-card-desc">Upload PDFs, TXT, or Markdown documents in the sidebar to perform grounded research with citations.</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with col_c:
        st.markdown(
            """
            <div class="hero-card">
                <div class="hero-card-icon">🌐</div>
                <div class="hero-card-title">Live Web Search</div>
                <div class="hero-card-desc">Integrates Tavily web search for real-time information retrieval and structured summary generation.</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    st.markdown("<br>", unsafe_allow_html=True)

# ───────────── CHAT HISTORY RENDER ───────────────────────────────────────────
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "user":
            st.write(message["content"])
        else:
            render_response(message["content"])

# ───────────── CHAT INPUT & EXECUTION ────────────────────────────────────────
CHAT_URL = f"{API_BASE_URL}/chat"

if prompt := st.chat_input("Ask your agent a question..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    payload = {
        "model_name": selected_model,
        "model_provider": provider,
        "system_prompt": SYSTEM_PROMPT,
        "messages": [prompt],
        "allow_search": allow_web_search,
        "use_tool_routing": use_tool_routing,
        "session_id": st.session_state.session_id,
    }

    with st.chat_message("assistant"):
        spinner_msg = "Routing & Generating Response..." if use_tool_routing else "Processing..."
        with st.status(spinner_msg, expanded=True) as status:
            try:
                response = requests.post(CHAT_URL, json=payload, timeout=120)
                if response.status_code == 200:
                    data = response.json()
                    if "error" in data:
                        status.update(label="Error occurred", state="error", expanded=False)
                        st.error(data["error"])
                    else:
                        status.update(label="Complete!", state="complete", expanded=False)
                        st.session_state.messages.append({"role": "assistant", "content": data})
                        st.rerun()
                else:
                    status.update(label="Server error", state="error", expanded=False)
                    st.error(f"! Server error {response.status_code}")
            except Exception as e:
                status.update(label="Connection error", state="error", expanded=False)
                st.error(f"! Connection error: {e}")
