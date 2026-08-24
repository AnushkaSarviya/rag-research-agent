# ─────────── IMPORTS ─────────────────────────────────────────────────────────
import os
import uuid
from datetime import date

import requests
import streamlit as st


# ─────────── API CONFIG ──────────────────────────────────────────────────────
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:9999")


# ─────────── PAGE CONFIG ─────────────────────────────────────────────────────
st.set_page_config(
    page_title="Agentic Studio",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ─────────── CUSTOM CSS ───────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="st-"] {
    font-family: 'Inter', -apple-system, sans-serif !important;
}
.stApp { background: #0D1117 !important; }
.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 5rem !important;
    max-width: 56rem !important;
}
p, span, li, td, th, label, div { color: #C9D1D9 !important; }

[data-testid="stSidebar"] {
    background: #161B22 !important;
    border-right: 1px solid #21262D !important;
}
[data-testid="stSidebar"] * { color: #C9D1D9 !important; }

.app-header {
    display: flex; align-items: center; gap: 0.75rem;
    padding: 0.5rem 0 1rem 0;
    border-bottom: 1px solid #21262D;
    margin-bottom: 1.25rem;
}
.app-header-title {
    font-size: 1.5rem; font-weight: 700;
    background: linear-gradient(135deg, #58A6FF 0%, #BC8CFF 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin: 0; line-height: 1;
}
.app-header-sub { font-size: 0.82rem; color: #6E7681 !important; margin-top: 0.15rem; }

.pill-row { display: flex; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 1.25rem; }
.pill {
    display: inline-flex; align-items: center; gap: 0.35rem;
    padding: 0.22rem 0.65rem; border-radius: 20px;
    font-size: 0.76rem; font-weight: 500;
    background: #161B22; border: 1px solid #21262D; color: #8B949E !important;
}
.pill-blue   { border-color: #1F6FEB44; color: #58A6FF !important; }
.pill-purple { border-color: #BC8CFF44; color: #BC8CFF !important; }
.pill-green  { border-color: #3FB95044; color: #3FB950 !important; }
.pill-gray   { border-color: #30363D;   color: #6E7681 !important; }

.stChatMessage {
    background: #161B22 !important;
    border: 1px solid #21262D !important;
    border-radius: 12px !important;
    padding: 1.1rem 1.3rem !important;
    margin-bottom: 0.75rem !important;
    box-shadow: none !important;
    animation: fadeUp 0.2s ease;
}
.stChatMessage:has([data-testid="chatAvatarIcon-user"])      { border-left: 2px solid #1F6FEB !important; }
.stChatMessage:has([data-testid="chatAvatarIcon-assistant"]) { border-left: 2px solid #BC8CFF !important; }
.stChatMessage p, .stChatMessage span, .stChatMessage li {
    color: #E6EDF3 !important; font-size: 0.91rem !important; line-height: 1.7 !important;
}
.stChatMessage strong { color: #F0F6FC !important; }
.stChatMessage code {
    background: #0D1117 !important; color: #79C0FF !important;
    padding: 0.1em 0.35em !important; border-radius: 4px !important;
    font-family: 'JetBrains Mono', monospace !important; font-size: 0.83em !important;
}
@keyframes fadeUp {
    from { opacity: 0; transform: translateY(6px); }
    to   { opacity: 1; transform: translateY(0); }
}

.tool-badge {
    display: inline-flex; align-items: center; gap: 0.4rem;
    padding: 0.25rem 0.7rem; border-radius: 20px;
    font-size: 0.76rem; font-weight: 600;
    margin-bottom: 0.5rem; letter-spacing: 0.01em;
}
.tb-research { background:#1F6FEB15; color:#58A6FF !important; border:1px solid #1F6FEB44; }
.tb-web      { background:#F7857515; color:#F78575 !important; border:1px solid #F7857544; }
.tb-notool   { background:#BC8CFF15; color:#BC8CFF !important; border:1px solid #BC8CFF44; }
.tool-hint {
    font-size: 0.77rem; color: #6E7681 !important;
    font-family: 'JetBrains Mono', monospace !important; margin-bottom: 0.75rem;
}

.hero-card {
    background: #161B22; border: 1px solid #21262D; border-radius: 12px;
    padding: 1.2rem; height: 100%;
    transition: border-color 0.2s ease, transform 0.2s ease;
}
.hero-card:hover { border-color: #388BFD55; transform: translateY(-2px); }
.hero-icon  { font-size: 1.4rem; margin-bottom: 0.5rem; }
.hero-title { font-weight: 700; color: #E6EDF3 !important; font-size: 0.95rem; margin-bottom: 0.3rem; }
.hero-desc  { color: #8B949E !important; font-size: 0.83rem; line-height: 1.55; }

.stChatInput > div {
    border-radius: 12px !important; border: 1px solid #30363D !important;
    background: #161B22 !important; transition: border-color 0.2s ease !important;
}
.stChatInput > div:focus-within { border-color: #388BFD !important; box-shadow: 0 0 0 3px #388BFD18 !important; }
.stChatInput textarea             { color: #E6EDF3 !important; }
.stChatInput textarea::placeholder{ color: #484F58 !important; }

.stButton > button {
    background: #21262D !important; color: #C9D1D9 !important;
    border: 1px solid #30363D !important; border-radius: 8px !important;
    font-weight: 500 !important; font-size: 0.84rem !important;
    transition: all 0.15s ease !important;
}
.stButton > button:hover { background: #30363D !important; border-color: #388BFD66 !important; color: #E6EDF3 !important; }

div[data-testid="stDownloadButton"] > button {
    background: #21262D !important; color: #C9D1D9 !important;
    border: 1px solid #30363D !important; border-radius: 8px !important;
    font-size: 0.84rem !important; font-weight: 500 !important;
    transition: all 0.15s ease !important;
}
div[data-testid="stDownloadButton"] > button:hover { border-color: #388BFD66 !important; background: #30363D !important; }

div[data-testid="stExpander"] {
    background: #161B22 !important; border: 1px solid #21262D !important;
    border-radius: 10px !important; margin-bottom: 0.6rem !important;
}
div[data-testid="stExpander"] summary { font-weight: 600 !important; color: #C9D1D9 !important; }
div[data-testid="stExpander"] summary:hover { color: #58A6FF !important; }
div[data-testid="stExpander"] p, div[data-testid="stExpander"] li { color: #C9D1D9 !important; }

div[data-testid="stFileUploader"] {
    border: 2px dashed #21262D !important; border-radius: 10px !important;
    background: #0D1117 !important; transition: border-color 0.2s ease !important;
}
div[data-testid="stFileUploader"]:hover { border-color: #388BFD55 !important; }

div[data-baseweb="select"] > div {
    background: #161B22 !important; border-color: #30363D !important;
    border-radius: 8px !important; color: #C9D1D9 !important;
}
div[data-baseweb="select"] > div:hover { border-color: #388BFD55 !important; }
div[data-baseweb="popover"]            { background: #161B22 !important; border: 1px solid #30363D !important; }

hr { border-color: #21262D !important; }
.stCaption, [data-testid="stCaptionContainer"] { color: #6E7681 !important; }
.stMarkdown a { color: #58A6FF !important; text-decoration: none; }
.stMarkdown a:hover { text-decoration: underline; }

.sb-brand-title {
    font-size: 1.15rem; font-weight: 700;
    background: linear-gradient(135deg, #58A6FF, #BC8CFF);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin: 0 0 0.15rem 0;
}
.sb-brand-sub { font-size: 0.76rem; color: #6E7681 !important; }
.sb-section {
    font-size: 0.72rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.08em; color: #6E7681 !important; margin-bottom: 0.6rem;
}

#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ─────────── TOOL BADGE HELPER ────────────────────────────────────────────────
TOOL_META = {
    "research_tool": ("📚", "tb-research", "RAG · Knowledge Base"),
    "web_search":    ("🌐", "tb-web",      "Web Search · Tavily"),
    "no_tool":       ("💬", "tb-notool",   "Direct LLM"),
}


def render_tool_badge(tool_decision: dict):
    tool       = tool_decision.get("tool", "no_tool")
    tool_input = tool_decision.get("input", "")
    icon, css, label = TOOL_META.get(tool, ("▪", "tb-notool", tool))
    st.markdown(
        f'<div class="tool-badge {css}">{icon} &nbsp;{label}</div>'
        f'<div class="tool-hint">&gt; {tool_input}</div>',
        unsafe_allow_html=True,
    )


# ─────────── RESPONSE RENDERER ────────────────────────────────────────────────
def render_response(data: dict):
    if "tool_decision" in data:
        render_tool_badge(data["tool_decision"])

    if data.get("summary"):
        st.markdown("**Summary**")
        for item in data["summary"]:
            st.markdown(f"- {item}")

    pc = data.get("pros_cons", {})
    if pc.get("pros") or pc.get("cons"):
        with st.expander("⚖️ Pros & Cons", expanded=True):
            c1, c2 = st.columns(2)
            with c1:
                if pc.get("pros"):
                    st.markdown("**✓ Pros**")
                    for pro in pc["pros"]:
                        st.markdown(f"- {pro}")
            with c2:
                if pc.get("cons"):
                    st.markdown("**✕ Cons**")
                    for con in pc["cons"]:
                        st.markdown(f"- {con}")

    if data.get("action_items"):
        with st.expander("📋 Action Items", expanded=True):
            for item in data["action_items"]:
                st.markdown(
                    f"- **{item.get('task','')}** "
                    f"— {item.get('assignee','Unassigned')} · {item.get('deadline','No deadline')}"
                )

    if data.get("citations"):
        with st.expander("📚 Sources", expanded=False):
            for c in data["citations"]:
                st.markdown(f"- `{c}`")

    if "latency" in data:
        st.caption(
            f"⏱ {data['latency']}s · {data.get('model_used','N/A')} · "
            f"Session `{str(data.get('session_id',''))[:8]}`"
        )


# ─────────── SESSION STATE ────────────────────────────────────────────────────
if "messages"       not in st.session_state:
    st.session_state.messages       = []
if "session_id"     not in st.session_state:
    st.session_state.session_id     = str(uuid.uuid4())
if "ingested_files" not in st.session_state:
    st.session_state.ingested_files = []


def build_chat_export() -> str:
    today = date.today().isoformat()
    lines = [f"## Chat Export — {st.session_state.session_id} — {today}", ""]
    for msg in st.session_state.messages:
        role, content = msg["role"], msg["content"]
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


# ─────────── SIDEBAR ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
        <div style="padding:0.5rem 0 1rem 0">
            <div class="sb-brand-title">✦ Agentic Studio</div>
            <div class="sb-brand-sub">RAG · Web Search · Memory</div>
        </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="sb-section">📡 Model</div>', unsafe_allow_html=True)
    provider = st.radio("Provider", ("Groq", "OpenRouter"), horizontal=True, label_visibility="collapsed")
    MODEL_MAP = {
        "Groq":       ["llama-3.3-70b-versatile", "mixtral-8x7b-32768"],
        "OpenRouter": ["meta-llama/llama-3.1-70b-instruct"],
    }
    selected_model = st.selectbox("Model", MODEL_MAP[provider], label_visibility="collapsed")

    st.markdown("---")
    st.markdown('<div class="sb-section">⚡ Engine</div>', unsafe_allow_html=True)
    allow_web_search = st.toggle("Web Search (Tavily)", value=True)
    use_tool_routing = st.toggle("Smart Tool Routing",  value=True)

    SYSTEM_PROMPT = (
        "You are an AI assistant that answers user queries using:\n"
        "1. Current query\n2. Short-term memory\n3. Long-term memory\n\n"
        "USER QUERY: {query}\n"
        "SHORT-TERM MEMORY: {chat_history}\n"
        "LONG-TERM MEMORY: {long_term_memory}\n\n"
        "Rules:\n"
        "- Use memory ONLY if relevant\n"
        "- Do NOT assume missing information\n"
        "- Do NOT mention memory sources\n"
        "- Provide a clear, concise, context-aware answer."
    )

    st.markdown("---")
    with st.expander("📁 Add Context (RAG)", expanded=False):
        if not st.session_state.ingested_files:
            st.caption("No documents ingested yet.")
        else:
            for entry in st.session_state.ingested_files:
                st.success(
                    f"✓ **{entry['filename']}**  \n"
                    f"`{entry['file_id'][:8]}…` · {entry['chunks_added']} chunks"
                )

        uploaded_file = st.file_uploader(
            "Upload PDF / TXT / MD",
            type=["pdf", "txt", "md"],
            label_visibility="collapsed",
        )
        if uploaded_file is not None:
            os.makedirs("scratch", exist_ok=True)
            temp_path = os.path.abspath(os.path.join("scratch", uploaded_file.name))
            with open(temp_path, "wb") as fh:
                fh.write(uploaded_file.getbuffer())

            if st.button("Ingest Document", use_container_width=True):
                with st.spinner("Ingesting into vector store…"):
                    try:
                        with open(temp_path, "rb") as fh:
                            resp = requests.post(
                                f"{API_BASE_URL}/ingest",
                                files={"file": (uploaded_file.name, fh, "application/octet-stream")},
                                timeout=60,
                            )
                        if resp.status_code == 200:
                            rd = resp.json()
                            if rd.get("status") == "success":
                                st.session_state.ingested_files.append({
                                    "filename":     uploaded_file.name,
                                    "file_id":      rd.get("file_id", "N/A"),
                                    "chunks_added": rd.get("chunks_added", 0),
                                })
                                st.rerun()
                            else:
                                st.error(f"Ingestion failed: {rd.get('message')}")
                        else:
                            st.error(f"Error {resp.status_code}: {resp.text}")
                    except Exception as e:
                        st.error(f"Connection error: {e}")

    st.markdown("---")
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("✕ Clear Chat", use_container_width=True):
            try:
                r = requests.delete(f"{API_BASE_URL}/history/{st.session_state.session_id}", timeout=10)
                if r.status_code not in (200, 204, 404):
                    st.warning(f"Backend returned {r.status_code}. Local chat cleared.")
            except Exception:
                pass
            st.session_state.messages   = []
            st.session_state.session_id = str(uuid.uuid4())
            st.rerun()
    with col_b:
        st.download_button(
            label="⬇ Export",
            data=build_chat_export(),
            file_name=f"chat_{st.session_state.session_id[:8]}_{date.today().isoformat()}.md",
            mime="text/markdown",
            use_container_width=True,
            disabled=len(st.session_state.messages) == 0,
        )

    st.markdown("---")
    st.caption(f"Session `{st.session_state.session_id[:8]}…`")


# ─────────── MAIN HEADER ──────────────────────────────────────────────────────
st.markdown("""
    <div class="app-header">
        <span style="font-size:1.6rem;background:linear-gradient(135deg,#58A6FF,#BC8CFF);-webkit-background-clip:text;-webkit-text-fill-color:transparent">✦</span>
        <div>
            <div class="app-header-title">Agentic Studio</div>
            <div class="app-header-sub">Autonomous RAG &amp; Multi-Tool Intelligence</div>
        </div>
    </div>
""", unsafe_allow_html=True)

routing_color = "pill-purple" if use_tool_routing else "pill-gray"
search_color  = "pill-green"  if allow_web_search  else "pill-gray"
st.markdown(f"""
    <div class="pill-row">
        <span class="pill pill-blue">📡 {selected_model.split("/")[-1]}</span>
        <span class="pill {routing_color}">⚡ Routing {"ON" if use_tool_routing else "OFF"}</span>
        <span class="pill {search_color}">🌐 Search {"ON" if allow_web_search else "OFF"}</span>
    </div>
""", unsafe_allow_html=True)


# ─────────── HERO (EMPTY STATE) ───────────────────────────────────────────────
if not st.session_state.messages:
    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    cards = [
        ("⚡", "Smart Routing",   "Automatically chooses between RAG, web search, or direct LLM."),
        ("📚", "RAG Engine",      "Upload PDFs, TXT, or Markdown in the sidebar for grounded answers."),
        ("🌐", "Live Web Search", "Tavily web search for real-time information and summaries."),
    ]
    for col, (icon, title, desc) in zip([c1, c2, c3], cards):
        with col:
            st.markdown(f"""
                <div class="hero-card">
                    <div class="hero-icon">{icon}</div>
                    <div class="hero-title">{title}</div>
                    <div class="hero-desc">{desc}</div>
                </div>
            """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)


# ─────────── CHAT HISTORY ─────────────────────────────────────────────────────
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "user":
            st.write(message["content"])
        else:
            render_response(message["content"])


# ─────────── CHAT INPUT & EXECUTION ──────────────────────────────────────────
if prompt := st.chat_input("Ask anything…"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    payload = {
        "model_name":       selected_model,
        "model_provider":   provider,
        "system_prompt":    SYSTEM_PROMPT,
        "messages":         [prompt],
        "allow_search":     allow_web_search,
        "use_tool_routing": use_tool_routing,
        "session_id":       st.session_state.session_id,
    }

    with st.chat_message("assistant"):
        label = "Routing & generating…" if use_tool_routing else "Processing…"
        with st.status(label, expanded=True) as status:
            try:
                response = requests.post(f"{API_BASE_URL}/chat", json=payload, timeout=120)
                if response.status_code == 200:
                    data = response.json()
                    if "error" in data:
                        status.update(label="Error", state="error", expanded=False)
                        st.error(data["error"])
                    else:
                        status.update(label="Done", state="complete", expanded=False)
                        st.session_state.messages.append({"role": "assistant", "content": data})
                        st.rerun()
                else:
                    status.update(label="Server error", state="error", expanded=False)
                    st.error(f"Server error {response.status_code}")
            except Exception as e:
                status.update(label="Connection error", state="error", expanded=False)
                st.error(f"Connection error: {e}")
