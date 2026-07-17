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
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

/* ── Reset ────────────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    color: #ececec;
}

/* ── Backgrounds & Layout ─────────────────────────── */
.stApp {
    background-color: #0e1117 !important;
}

/* Main app padding for minimalism */
.block-container {
    padding-top: 3rem !important;
    padding-bottom: 5rem !important;
    max-width: 48rem !important; /* Keep chat centered and readable */
}

/* ── Sidebar ──────────────────────────────────── */
[data-testid="stSidebar"] {
    background-color: #161b22 !important;
    border-right: 1px solid #30363d;
}

[data-testid="stSidebar"] * {
    color: #c9d1d9 !important;
}

[data-testid="stSidebar"] h1, 
[data-testid="stSidebar"] h2, 
[data-testid="stSidebar"] h3 {
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #8b949e !important;
}

/* ── Typography ───────────────────────────────── */
h1 {
    color: #f0f6fc !important;
    font-size: 2.2rem !important;
    font-weight: 600 !important;
    letter-spacing: -0.03em;
    margin-bottom: 1.5rem !important;
}

h3 {
    font-size: 1rem !important;
    font-weight: 600 !important;
    margin-top: 1rem !important;
    margin-bottom: 0.5rem !important;
}

/* ── Chat messages ────────────────────────────── */
.stChatMessage {
    background: transparent !important;
    border: none !important;
    padding: 0.5rem 0 !important;
    margin-bottom: 1rem;
    border-radius: 0;
}

/* ── Buttons ──────────────────────────────────── */
.stButton > button {
    background-color: #21262d !important;
    color: #c9d1d9 !important;
    border: 1px solid rgba(240, 246, 252, 0.1) !important;
    border-radius: 6px !important;
    font-weight: 500 !important;
    transition: all 0.2s ease;
}

.stButton > button:hover {
    background-color: #30363d !important;
    border-color: #8b949e !important;
}

/* ── Expanders ────────────────────────────────── */
div[data-testid="stExpander"] {
    border: 1px solid #30363d !important;
    border-radius: 8px !important;
    background-color: #161b22 !important;
    box-shadow: none !important;
}

/* ── Inputs ───────────────────────────────────── */
.stTextInput>div>div>input, .stChatInput>div {
    border-radius: 8px !important;
    border: 1px solid #30363d !important;
    background-color: #161b22 !important;
}
.stChatInput>div:focus-within {
    border-color: #58a6ff !important;
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
# ───────────── STATE INIT ────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []


# ───────────── SIDEBAR CONFIG ────────────────────────────────────────────────
with st.sidebar:
    st.markdown("<h2 style='margin-top: 0; margin-bottom: 0.2rem; color: #f0f6fc; font-weight: 600;'>◆ Agentic Studio</h2>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 0.8rem; color: #8b949e; margin-bottom: 1.5rem;'>Production-Grade RAG Assistant</p>", unsafe_allow_html=True)

    st.markdown("### Model Configuration")
    provider = st.radio("📡 Provider", ("Groq", "OpenRouter"), horizontal=True, label_visibility="collapsed")
    MODEL_NAMES_GROQ = ["llama-3.3-70b-versatile", "mixtral-8x7b-32768"]
    MODEL_NAMES_OPENROUTER = ["meta-llama/llama-3.1-70b-instruct"]
    selected_model = st.selectbox(
        "Model", 
        MODEL_NAMES_GROQ if provider == "Groq" else MODEL_NAMES_OPENROUTER,
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.markdown("### Engine Capabilities")
    allow_web_search = st.toggle("Enable Web Search (Tavily)", value=True)
    use_tool_routing = st.toggle("Enable Smart Routing", value=True)

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

    st.markdown("---")
    with st.expander("📁 Add Context (RAG)", expanded=False):
        uploaded_file = st.file_uploader(
            "Upload reference document",
            type=["pdf", "txt", "md"],
            help="Upload a PDF, TXT, or MD file to add to the RAG knowledge base.",
            label_visibility="collapsed"
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
                        with open(temp_path, "rb") as f:
                            files = {"file": (uploaded_file.name, f, "application/octet-stream")}
                            resp = requests.post(ingest_url, files=files, timeout=60)
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

# ───────────── MAIN LAYOUT ───────────────────────────────────────────────────
# Header status bar representing current configuration
c1, c2 = st.columns([8, 2])
with c1:
    st.markdown(
        f"<span style='color: #8b949e; font-size: 0.85rem;'>Active: <strong>{selected_model}</strong></span>",
        unsafe_allow_html=True
    )
with c2:
    st.markdown(
        f"<span style='color: #8b949e; font-size: 0.85rem; float: right;'>Routing: <strong>{'ON' if use_tool_routing else 'OFF'}</strong></span>",
        unsafe_allow_html=True
    )
st.markdown("---")

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
