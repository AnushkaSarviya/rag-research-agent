import streamlit as st
import requests
import json
from streamlit_lottie import st_lottie

# ------------------- PAGE CONFIG --------------------
st.set_page_config(page_title="Agentic Studio", page_icon="✨", layout="wide", initial_sidebar_state="expanded")

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

/* Hide Streamlit Branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ------------------- STATE INIT ---------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ------------------- SIDEBAR CONFIG -----------------
with st.sidebar:
    st.markdown("<div class='sidebar-heading'>⚙️ Configuration</div>", unsafe_allow_html=True)
    st.markdown("---")
    
    provider = st.radio("📡 Provider", ("Groq", "OpenRouter"), horizontal=True)
    
    MODEL_NAMES_GROQ = ["llama-3.3-70b-versatile", "mixtral-8x7b-32768"]
    MODEL_NAMES_OPENROUTER = ["meta-llama/llama-3.1-70b-instruct"]
    
    if provider == "Groq":
        selected_model = st.selectbox("🤖 Model", MODEL_NAMES_GROQ)
    else:
        selected_model = st.selectbox("🤖 Model", MODEL_NAMES_OPENROUTER)
        
    allow_web_search = st.toggle("🌐 Enable Web Search", value=True)
    
    st.markdown("---")
    SYSTEM_PROMPT = st.text_area(
        "🧠 System Prompt",
        value="You are a Research & Summarization Agent. Be concise, factual, and professional.",
        height=150
    )
    
    st.markdown("---")
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# ------------------- MAIN LAYOUT -------------------
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if lottie_ai:
        st_lottie(lottie_ai, height=120, key="ai_robot")
        
st.markdown("<h1>Agentic Studio</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Experience the next generation of AI Research & Summarization</p>", unsafe_allow_html=True)

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "user":
            st.write(message["content"])
        else:
            # Render structured response
            data = message["content"]
            if "summary" in data and data["summary"]:
                st.markdown("### 📝 Summary")
                for item in data["summary"]:
                    st.markdown(f"- {item}")

            if "pros_cons" in data and (data["pros_cons"].get("pros") or data["pros_cons"].get("cons")):
                c1, c2 = st.columns(2)
                with c1:
                    if data["pros_cons"].get("pros"):
                        st.markdown("### ✅ Pros")
                        for pro in data["pros_cons"]["pros"]:
                            st.markdown(f"- {pro}")
                with c2:
                    if data["pros_cons"].get("cons"):
                        st.markdown("### ❌ Cons")
                        for con in data["pros_cons"]["cons"]:
                            st.markdown(f"- {con}")

            if "action_items" in data and data["action_items"]:
                st.markdown("### 📋 Action Items")
                for item in data["action_items"]:
                    assignee = item.get("assignee", "Unassigned")
                    task = item.get("task", "")
                    deadline = item.get("deadline", "No deadline")
                    st.markdown(f"- **{task}** (Assignee: {assignee}, Deadline: {deadline})")

            if "citations" in data and data["citations"]:
                st.markdown("### 📚 Citations")
                for citation in data["citations"]:
                    st.markdown(f"- `{citation}`")
            
            if "latency" in data:
                st.caption(f"⚡ Response time: {data['latency']}s | 🤖 Model: {data.get('model_used', 'N/A')}")

# ------------------- CHAT INPUT --------------------
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
        "allow_search": allow_web_search
    }

    # Fetch response
    with st.chat_message("assistant"):
        with st.spinner("Analyzing and researching... 🔮"):
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
                    st.error(f"❌ Server error {response.status_code}. Check backend logs.")
            
            except requests.exceptions.ConnectionError:
                st.error("❌ Cannot connect to the backend. Make sure the FastAPI server is running on port 9999.")
            except requests.exceptions.Timeout:
                st.error("⏱️ Request timed out. The agent is taking too long to respond.")
