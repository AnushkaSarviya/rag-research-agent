import subprocess
import sys
# ───────────── AUTO-INSTALL DEPENDENCIES ─────────────────────────────────────
REQUIRED = [
    "streamlit",
    "requests",
    "streamlit-lottie",
]

for package in REQUIRED:
    try:
        __import__(package.replace("-", "_"))
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# ───────────── IMPORTS ───────────────────────────────────────────────────────
import streamlit as st  # noqa: E402
import requests  # noqa: E402
from streamlit_lottie import st_lottie  # noqa: E402


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


# ───────────── CUSTOM CSS ───────────────────────────────────────────────────
custom_css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ── Reset ────────────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    color: #c9d1d9;
}

/* ── Ombre background & Glows ─────────────────────────── */
.stApp {
    background: linear-gradient(168deg, #0a0a0f 0%, #0d1117 30%, #111827 60%, #0d1117 100%) !important;
    background-attachment: fixed !important;
}

.stApp::before {
    content: '';
    position: fixed;
    top: -40%;
    left: 50%;
    transform: translateX(-50%);
    width: 80vw;
    height: 60vh;
    background: radial-gradient(ellipse, rgba(99,102,241,0.06) 0%, transparent 70%);
    pointer-events: none;
    z-index: 0;
}

/* ── Sidebar ──────────────────────────────────── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, rgba(10,10,15,0.97) 0%, rgba(13,17,23,0.97) 100%) !important;
    border-right: 1px solid rgba(255,255,255,0.04);
}

[data-testid="stSidebar"] * {
    color: #8b949e !important;
}

[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stRadio label,
[data-testid="stSidebar"] .stTextArea label {
    color: #8b949e !important;
    font-weight: 500;
    font-size: 0.82rem;
    letter-spacing: 0.3px;
}

/* ── Typography ───────────────────────────────── */
h1 {
    text-align: center;
    color: #e6edf3 !important;
    font-size: 3rem !important;
    font-weight: 800 !important;
    letter-spacing: -1px;
    margin-bottom: 0.2rem !important;
    background: linear-gradient(135deg, #00f2fe 0%, #4facfe 50%, #00c6ff 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent !important;
    text-shadow: 0 0 40px rgba(0, 242, 254, 0.2);
}

h3 {
    color: #8b949e !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    margin-top: 1.2rem !important;
    margin-bottom: 0.6rem !important;
}

.sidebar-heading {
    text-align: center;
    color: #c9d1d9 !important;
    font-size: 1.1rem;
    font-weight: 600;
    letter-spacing: 0.5px;
    margin-bottom: 0.5rem;
}

/* ── Chat messages ────────────────────────────── */
.stChatMessage {
    background: rgba(22, 27, 34, 0.5) !important;
    border-radius: 12px;
    border: 1px solid rgba(255,255,255,0.08) !important;
    padding: 1rem;
    margin-bottom: 0.8rem;
    backdrop-filter: blur(10px);
}

/* ── Tool decision badges ──────── */
.tool-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 16px;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    margin-bottom: 10px;
}

.tool-badge-research {
    background: rgba(99,102,241,0.12);
    color: #818cf8;
    border: 1px solid rgba(99,102,241,0.25);
    box-shadow: 0 0 20px rgba(99,102,241,0.1);
}

.tool-badge-web {
    background: rgba(52,211,153,0.1);
    color: #6ee7b7;
    border: 1px solid rgba(52,211,153,0.25);
    box-shadow: 0 0 20px rgba(52,211,153,0.1);
}

.tool-badge-notool {
    background: rgba(139,148,158,0.08);
    color: #94a3b8;
    border: 1px solid rgba(139,148,158,0.2);
}

.tool-input-hint {
    font-size: 0.72rem;
    color: #6e7681;
    margin-bottom: 15px;
    font-style: italic;
}

/* ── Buttons ──────────────────────────────────── */
.stButton > button {
    background: rgba(30, 41, 59, 0.7) !important;
    color: #f1f5f9 !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 10px !important;
    transition: all 0.3s ease;
}

.stButton > button:hover {
    background: rgba(51, 65, 85, 0.9) !important;
    border-color: #38bdf8 !important;
    box-shadow: 0 0 15px rgba(56, 189, 248, 0.2);
}

/* ── Hide branding ────────────────────────────── */
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
        <div class="tool-input-hint">> Extracted input: <em>"{tool_input}"</em></div>
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

    if "latency" in data:
        st.caption(
            f"~ {data['latency']}s | "
            f"Model: {data.get('model_used', 'N/A')} | "
            f"Session: {data.get('session_id', 'N/A')}"
        )


# ───────────── STATE INIT ────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "show_sidebar" not in st.session_state:
    st.session_state.show_sidebar = True


# ───────────── SIDEBAR CONFIG ────────────────────────────────────────────────
with st.sidebar:
    st.markdown("<div class='sidebar-heading'>≡ Configuration</div>", unsafe_allow_html=True)
    st.markdown("---")

    with st.expander("▪ Model Selection", expanded=True):
        provider = st.radio("📡 Provider", ("Groq", "OpenRouter"), horizontal=True)
        MODEL_NAMES_GROQ = ["llama-3.3-70b-versatile", "mixtral-8x7b-32768"]
        MODEL_NAMES_OPENROUTER = ["meta-llama/llama-3.1-70b-instruct"]
        selected_model = st.selectbox("Model", MODEL_NAMES_GROQ if provider == "Groq" else MODEL_NAMES_OPENROUTER)

    with st.expander("≡ Tool Settings", expanded=False):
        allow_web_search = st.toggle("Enable Web Search", value=True)
        use_tool_routing = st.toggle("Enable Tool Router", value=True)

    # Default Advanced System Prompt used for backend communication
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

    with st.expander("📁 Document Ingestion (RAG)", expanded=False):
        uploaded_file = st.file_uploader(
            "Upload reference document",
            type=["pdf", "txt", "md"],
            help="Upload a PDF, TXT, or MD file to add to the RAG knowledge base."
        )
        if uploaded_file is not None:
            import os
            os.makedirs("scratch", exist_ok=True)
            temp_path = os.path.abspath(os.path.join("scratch", uploaded_file.name))
            with open(temp_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            if st.button("Ingest Document", use_container_width=True):
                with st.spinner("Ingesting into vector store..."):
                    try:
                        ingest_url = "http://127.0.0.1:9999/ingest"
                        resp = requests.post(ingest_url, params={"file_path": temp_path}, timeout=60)
                        if resp.status_code == 200:
                            res_data = resp.json()
                            if res_data.get("status") == "success":
                                st.success(f"Ingested {res_data.get('chunks_added')} chunks!")
                            else:
                                st.error(f"Ingestion failed: {res_data.get('message')}")
                        else:
                            st.error(f"Error {resp.status_code}: {resp.text}")
                    except Exception as e:
                        st.error(f"Connection error: {e}")

    st.markdown("---")
    if st.button("x Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

if not st.session_state.show_sidebar:
    st.markdown("<style>div[data-testid='stSidebar'] {display: none !important;}</style>", unsafe_allow_html=True)
    st.markdown("<style>section[data-testid='stSidebar'] {display: none !important;}</style>", unsafe_allow_html=True)

# ───────────── MAIN LAYOUT ───────────────────────────────────────────────────
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if lottie_ai:
        st_lottie(lottie_ai, height=120, key="ai_robot")

c1, c2 = st.columns([8, 2])
with c2:
    if st.button("≡ Settings" if not st.session_state.show_sidebar else "x Hide", use_container_width=True):
        st.session_state.show_sidebar = not st.session_state.show_sidebar
        st.rerun()

st.markdown("<h1>Agentic Studio</h1>", unsafe_allow_html=True)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "user":
            st.write(message["content"])
        else:
            render_response(message["content"])

# ───────────── CHAT INPUT ────────────────────────────────────────────────────
API_URL = "http://127.0.0.1:9999/chat"

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
    }

    with st.chat_message("assistant"):
        spinner_msg = "Routing & Generating Response..." if use_tool_routing else "Processing..."
        with st.status(spinner_msg, expanded=True) as status:
            try:
                response = requests.post(API_URL, json=payload, timeout=120)
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
