import streamlit as st
import requests
import json
from streamlit_lottie import st_lottie

# ------------------- PAGE CONFIG --------------------
st.set_page_config(page_title="Agentic Studio", page_icon="✦", layout="wide", initial_sidebar_state="expanded")

# ------------------- HELPER FUNCTIONS ----------------
def load_lottieurl(url: str):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

# Lottie animation for AI
lottie_ai = load_lottieurl("https://assets3.lottiefiles.com/packages/lf20_dbbxfnjo.json")

# ------------------- CUSTOM CSS ---------------------
custom_css = """
<style>
/* App Background & Typography */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');

html, body, [class*="css"]  {
    font-family: 'Inter', sans-serif;
}

/* Aesthetic Dark Background */
.stApp {
    background-color: #0d1117 !important;
    background-image: radial-gradient(ellipse at 50% -20%, #1f2937, #0d1117 80%) !important;
    background-attachment: fixed !important;
}

/* Sidebar styling */
[data-testid="stSidebar"] {
    background: rgba(15, 23, 42, 0.95) !important;
    backdrop-filter: blur(20px);
    border-right: 1px solid rgba(255, 255, 255, 0.1);
}

/* Gradient Title */
h1 {
    text-align: center;
    background: linear-gradient(135deg, #00f2fe 0%, #4facfe 50%, #00c6ff 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 3.8rem !important;
    font-weight: 900 !important;
    margin-bottom: 0.1em;
    letter-spacing: -1px;
    filter: drop-shadow(0 0 15px rgba(0, 242, 254, 0.4));
}

.subtitle {
    text-align: center;
    font-size: 1.25rem;
    background: linear-gradient(135deg, #89f7fe 0%, #66a6ff 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 2.5rem;
    font-weight: 600;
    letter-spacing: 0.5px;
}

/* Sidebar heading */
.sidebar-heading {
    text-align: center;
    background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 1.8rem;
    font-weight: 800;
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
}

/* Glassmorphism Cards */
.glass-card {
    background: rgba(30, 41, 59, 0.7);
    padding: 20px;
    border-radius: 16px;
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.08);
    box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
    margin-bottom: 1.5rem;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.glass-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 40px rgba(0, 242, 254, 0.15);
    border: 1px solid rgba(0, 242, 254, 0.3);
}

/* Chat Messages */
.stChatMessage {
    background: rgba(30, 41, 59, 0.4) !important;
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.05);
    padding: 1rem;
    margin-bottom: 1rem;
}

/* Glow effects for success/info text */
.glow-text {
    color: #38bdf8;
    text-shadow: 0 0 10px rgba(56, 189, 248, 0.4);
    font-weight: 600;
}

/* ── Tool Decision Badge ─────────────────────────────────── */
.tool-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px 14px;
    border-radius: 999px;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.4px;
    margin-bottom: 12px;
    border: 1px solid;
}

.tool-badge-research {
    background: rgba(79, 172, 254, 0.15);
    color: #4facfe;
    border-color: rgba(79, 172, 254, 0.4);
    box-shadow: 0 0 12px rgba(79, 172, 254, 0.2);
}

.tool-badge-web {
    background: rgba(52, 211, 153, 0.15);
    color: #34d399;
    border-color: rgba(52, 211, 153, 0.4);
    box-shadow: 0 0 12px rgba(52, 211, 153, 0.2);
}

.tool-badge-notool {
    background: rgba(148, 163, 184, 0.12);
    color: #94a3b8;
    border-color: rgba(148, 163, 184, 0.3);
}

.tool-input-hint {
    font-size: 0.72rem;
    color: #64748b;
    margin-bottom: 10px;
    font-style: italic;
}

/* Hide Streamlit Branding */
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
    """Render a pill badge showing which tool the router selected."""
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
    """Render the structured agent response, including tool decision badge."""

    # Show tool routing badge if present
    if "tool_decision" in data:
        render_tool_badge(data["tool_decision"])

    if "summary" in data and data["summary"]:
        st.markdown("### ≡ Summary")
        for item in data["summary"]:
            st.markdown(f"- {item}")

    if "pros_cons" in data and (
        data["pros_cons"].get("pros") or data["pros_cons"].get("cons")
    ):
        c1, c2 = st.columns(2)
        with c1:
            if data["pros_cons"].get("pros"):
                st.markdown("### ✓ Pros")
                for pro in data["pros_cons"]["pros"]:
                    st.markdown(f"- {pro}")
        with c2:
            if data["pros_cons"].get("cons"):
                st.markdown("### ✕ Cons")
                for con in data["pros_cons"]["cons"]:
                    st.markdown(f"- {con}")

    if "action_items" in data and data["action_items"]:
        st.markdown("### ▪ Action Items")
        for item in data["action_items"]:
            assignee = item.get("assignee", "Unassigned")
            task = item.get("task", "")
            deadline = item.get("deadline", "No deadline")
            st.markdown(f"- **{task}** (Assignee: {assignee}, Deadline: {deadline})")

    if "citations" in data and data["citations"]:
        st.markdown("### * Citations")
        for citation in data["citations"]:
            st.markdown(f"- `{citation}`")

    if "latency" in data:
        st.caption(
            f"~ Response time: {data['latency']}s | "
            f"| Model: {data.get('model_used', 'N/A')} | "
            f"| Session: {data.get('session_id', 'N/A')}"
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

        if provider == "Groq":
            selected_model = st.selectbox("Model", MODEL_NAMES_GROQ)
        else:
            selected_model = st.selectbox("Model", MODEL_NAMES_OPENROUTER)

    with st.expander("≡ Tool Settings", expanded=False):
        allow_web_search = st.toggle("Enable Web Search", value=True)

        # ── Tool Router toggle ───────────────────────────────────────────────────
        use_tool_routing = st.toggle(
            "Enable Tool Router",
            value=True,
            help=(
                "When ON, a dedicated LLM step first decides which tool (RAG, Web Search, "
                "or none) to use before answering. This makes tool selection explicit and "
                "transparent. Turn OFF to use the classic ReAct agent loop instead."
            ),
        )

        if use_tool_routing:
            st.caption("On: Tool Router active.")
        else:
            st.caption("Off: Tool Router disabled.")

    with st.expander("▪ Prompt Engineering", expanded=False):
        SYSTEM_PROMPT = st.text_area(
            "System Prompt",
            value="You are a Research & Summarization Agent. Be concise, factual, and professional.",
            height=150
        )

    st.markdown("---")
    if st.button("x Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# Apply CSS to hide sidebar if toggled off
if not st.session_state.show_sidebar:
    st.markdown("<style>div[data-testid='stSidebar'] {display: none !important;}</style>", unsafe_allow_html=True)
    st.markdown("<style>section[data-testid='stSidebar'] {display: none !important;}</style>", unsafe_allow_html=True)

# ───────────── MAIN LAYOUT ───────────────────────────────────────────────────
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if lottie_ai:
        st_lottie(lottie_ai, height=120, key="ai_robot")

# Custom Sidebar Toggle in Main Area
c1, c2 = st.columns([8, 2])
with c2:
    if st.button("≡ Show Settings" if not st.session_state.show_sidebar else "x Hide Settings", use_container_width=True):
        st.session_state.show_sidebar = not st.session_state.show_sidebar
        st.rerun()

st.markdown("<h1>Agentic Studio</h1>", unsafe_allow_html=True)

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "user":
            st.write(message["content"])
        else:
            render_response(message["content"])

# ───────────── CHAT INPUT ────────────────────────────────────────────────────
API_URL = "http://127.0.0.1:9999/chat"

if prompt := st.chat_input("Ask your agent a question or request research..."):
    # Add user message to state and display
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # Prepare request
    payload = {
        "model_name": selected_model,
        "model_provider": provider,
        "system_prompt": SYSTEM_PROMPT,
        "messages": [prompt],
        "allow_search": allow_web_search,
        "use_tool_routing": use_tool_routing,   # send router toggle state
    }

    # Fetch response
    with st.chat_message("assistant"):
        spinner_msg = (
            "> Routing query to best tool… then researching…"
            if use_tool_routing
            else "Analyzing and researching..."
        )
        with st.spinner(spinner_msg):
            try:
                response = requests.post(API_URL, json=payload, timeout=120)

                if response.status_code == 200:
                    data = response.json()
                    if "error" in data:
                        st.error(data["error"])
                    else:
                        # Append assistant response and force rerun to render cleanly
                        st.session_state.messages.append({"role": "assistant", "content": data})
                        st.rerun()
                else:
                    st.error(f"! Server error {response.status_code}. Check backend logs.")

            except requests.exceptions.ConnectionError:
                st.error("! Cannot connect to the backend. Make sure the FastAPI server is running on port 9999.")
            except requests.exceptions.Timeout:
                st.error("! Request timed out. The agent is taking too long to respond.")
