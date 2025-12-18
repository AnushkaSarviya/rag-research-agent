import streamlit as st
import requests
from streamlit.components.v1 import html

# ------------------- PAGE CONFIG --------------------
st.set_page_config(page_title="AI Agent Studio", layout="wide")

# ------------------- CUSTOM CSS ---------------------
custom_css = """
<style>
/* Gradient Title */
h1 {
    text-align: center;
    background: linear-gradient(90deg, #6a11cb, #2575fc);
    -webkit-background-clip: text;
    color: transparent;
    font-size: 3rem !important;
    font-weight: 900 !important;
    margin-bottom: 0.2em;
}

/* Subtle fade animation for sections */
.block-container {
    animation: fadeIn 1.2s ease;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0px); }
}

/* Glass card */
.glass-card {
    background: rgba(255, 255, 255, 0.15);
    padding: 25px;
    border-radius: 15px;
    backdrop-filter: blur(15px);
    border: 1px solid rgba(255, 255, 255, 0.3);
}

/* Buttons */
.stButton>button {
    width: 100%;
    border-radius: 12px;
    padding: 0.8rem 1rem;
    font-size: 1.1rem;
    font-weight: 600;
    background: linear-gradient(90deg, #6a11cb, #2575fc);
    border: none;
    color: white;
    transition: 0.3s;
}

.stButton>button:hover {
    transform: scale(1.03);
    background: linear-gradient(90deg, #5a01bb, #1a63e8);
}

/* Radio buttons styling */
div[role="radiogroup"] > label {
    background: rgba(255,255,255,0.08);
    padding: 10px 20px;
    border-radius: 10px;
    margin-bottom: 6px;
}
</style>
"""

st.markdown(custom_css, unsafe_allow_html=True)

# ------------------- HEADER ------------------------
st.markdown("<h1>AI Agent Studio</h1>", unsafe_allow_html=True)
st.write("<p style='text-align:center; font-size:18px;'>Build, Customize & Chat with Advanced AI Agents</p>", unsafe_allow_html=True)

# ------------------- LAYOUT ------------------------
col1, col2 = st.columns([1.2, 1])

with col1:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)

    st.subheader("🔧 Agent Configuration")

    SYSTEM_PROMPT = st.text_area(
        "🧠 System Prompt",
        placeholder="Describe how your agent should behave...",
        height=120
    )

    provider=st.radio("Select Provider:", ("Groq", "OpenRouter"))

    MODEL_NAMES_GROQ = ["llama-3.3-70b-versatile", "mixtral-8x7b-32768"]
    MODEL_NAMES_OPENROUTER = ["meta-llama/llama-3.1-70b-instruct"]

    if provider == "Groq":
        selected_model = st.selectbox("🤖 Select Groq Model:", MODEL_NAMES_GROQ)
    else:
        selected_model = st.selectbox("🤖 Select OpenRouter Model:", MODEL_NAMES_OPENROUTER)

    allow_web_search = st.checkbox("🌐 Allow Web Search")

    st.markdown("</div>", unsafe_allow_html=True)

with col2:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)

    st.subheader("💬 Ask Your Agent")
    user_query = st.text_area("Your Question:", height=180, placeholder="Type your query here...")

    st.markdown("</div>", unsafe_allow_html=True)

st.write("")
ask = st.button("🚀 Ask Agent!")

API_URL = "http://127.0.0.1:9999/chat"

# ------------------- SEND QUERY ------------------------
if ask:
    if not user_query.strip():
        st.warning("Please enter a question!")
    else:
        payload = {
            "model_name": selected_model,
            "model_provider": provider,
            "system_prompt": SYSTEM_PROMPT,
            "messages": [user_query],
            "allow_search": allow_web_search
        }

        with st.spinner("Thinking... 🤖💬"):
            response = requests.post(API_URL, json=payload)

        st.subheader("✨ Agent Response")

        if response.status_code == 200:
            data = response.json()

            if "error" in data:
                st.error(data["error"])
            else:
                # Display structured response
                if "summary" in data and data["summary"]:
                    st.markdown("### 📝 Summary")
                    for item in data["summary"]:
                        st.markdown(f"- {item}")
                
                if "pros_cons" in data and data["pros_cons"]:
                    col1, col2 = st.columns(2)
                    with col1:
                        if data["pros_cons"].get("pros"):
                            st.markdown("### ✅ Pros")
                            for pro in data["pros_cons"]["pros"]:
                                st.markdown(f"- {pro}")
                    with col2:
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
                
                # Show metadata
                if "latency" in data:
                    st.caption(f"⏱️ Response time: {data['latency']}s | Model: {data.get('model_used', 'N/A')}")
                
                # Fallback: if response is just a string (plain chatbot mode)
                if not any(key in data for key in ["summary", "pros_cons", "action_items", "citations"]):
                    # Display as plain text
                    response_text = str(data.get("summary", data.get("response", data)))
                    st.markdown(f"**Response:**\n\n{response_text}")
        else:
            st.error("Server error. Check backend.")
