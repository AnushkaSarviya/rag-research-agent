# ─────────── IMPORTS ─────────────────────────────────────────────────────────
import os
import uuid
from datetime import date

import requests
import streamlit as st


# ─────────── API CONFIG ──────────────────────────────────────────────────────
# Use BACKEND_URL env var for deployment; falls back to local dev default.
API_BASE_URL = os.getenv("BACKEND_URL", os.getenv("API_BASE_URL", "http://127.0.0.1:9999"))


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
/* ── Typography ──────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="st-"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}

/* ── Global background ───────────────────────────────────────── */
.stApp { background: #0F1318 !important; }

/* ── Main container ──────────────────────────────────────────── */
.block-container {
    padding-top: 1.25rem !important;
    padding-bottom: 4rem !important;
    max-width: 52rem !important;
}

/* ── Base text ───────────────────────────────────────────────── */
p, span, li, td, th, label, div { color: #C9D1D9 !important; }

/* ── Scrollbar ───────────────────────────────────────────────── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: #2D333B; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #444C56; }

/* ── Sidebar ─────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: #161B22 !important;
    border-right: 1px solid rgba(48, 54, 61, 0.6) !important;
}
[data-testid="stSidebar"] * { color: #C9D1D9 !important; }
[data-testid="stSidebar"] .stMarkdown hr {
    margin: 0.6rem 0 !important;
    border-color: rgba(48, 54, 61, 0.5) !important;
}

/* ── App header ──────────────────────────────────────────────── */
.app-header {
    display: flex;
    align-items: center;
    gap: 0.65rem;
    padding: 0.15rem 0 0.7rem 0;
    border-bottom: 1px solid rgba(48, 54, 61, 0.5);
    margin-bottom: 0.75rem;
}
.app-header-icon {
    font-size: 1.2rem;
    line-height: 1;
    background: linear-gradient(135deg, #4D94E6 0%, #8B6DC4 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.app-header-title {
    font-size: 1.1rem;
    font-weight: 700;
    color: #E6EDF3 !important;
    margin: 0;
    line-height: 1.2;
    letter-spacing: -0.01em;
}
.app-header-sub {
    font-size: 0.74rem;
    color: #6E7681 !important;
    margin-top: 0.05rem;
    font-weight: 400;
}

/* ── Status pills ────────────────────────────────────────────── */
.pill-row {
    display: flex;
    gap: 0.35rem;
    flex-wrap: wrap;
    margin-bottom: 0.85rem;
}
.pill {
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    padding: 0.15rem 0.5rem;
    border-radius: 5px;
    font-size: 0.7rem;
    font-weight: 500;
    background: rgba(22, 27, 34, 0.8);
    border: 1px solid rgba(48, 54, 61, 0.6);
    color: #8B949E !important;
    letter-spacing: 0.01em;
}
.pill-blue   { border-color: rgba(31, 111, 235, 0.2); color: #4D94E6 !important; }
.pill-purple { border-color: rgba(139, 109, 196, 0.2); color: #8B6DC4 !important; }
.pill-green  { border-color: rgba(63, 185, 80, 0.2);  color: #3FB950 !important; }
.pill-gray   { border-color: rgba(48, 54, 61, 0.6);   color: #484F58 !important; }

/* ── Chat messages ───────────────────────────────────────────── */
.stChatMessage {
    background: #161B22 !important;
    border: 1px solid rgba(48, 54, 61, 0.5) !important;
    border-radius: 8px !important;
    padding: 0.85rem 1.1rem !important;
    margin-bottom: 0.5rem !important;
    box-shadow: none !important;
    animation: fadeUp 0.18s ease-out;
}
.stChatMessage:has([data-testid="chatAvatarIcon-user"]) {
    border-left: 2px solid rgba(77, 148, 230, 0.6) !important;
}
.stChatMessage:has([data-testid="chatAvatarIcon-assistant"]) {
    border-left: 2px solid rgba(139, 109, 196, 0.6) !important;
}
.stChatMessage p,
.stChatMessage span,
.stChatMessage li {
    color: #E6EDF3 !important;
    font-size: 0.87rem !important;
    line-height: 1.65 !important;
}
.stChatMessage strong { color: #F0F6FC !important; }
.stChatMessage code {
    background: #0F1318 !important;
    color: #79C0FF !important;
    padding: 0.1em 0.3em !important;
    border-radius: 4px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.82em !important;
    border: 1px solid rgba(48, 54, 61, 0.5) !important;
}
@keyframes fadeUp {
    from { opacity: 0; transform: translateY(3px); }
    to   { opacity: 1; transform: translateY(0); }
}

/* ── Tool badges ─────────────────────────────────────────────── */
.tool-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    padding: 0.15rem 0.5rem;
    border-radius: 5px;
    font-size: 0.72rem;
    font-weight: 600;
    margin-bottom: 0.3rem;
    letter-spacing: 0.01em;
}
.tb-research { background: rgba(31, 111, 235, 0.06); color: #4D94E6 !important; border: 1px solid rgba(31, 111, 235, 0.15); }
.tb-web      { background: rgba(247, 133, 117, 0.06); color: #E07B6C !important; border: 1px solid rgba(247, 133, 117, 0.15); }
.tb-notool   { background: rgba(139, 109, 196, 0.06); color: #8B6DC4 !important; border: 1px solid rgba(139, 109, 196, 0.15); }
.tool-hint {
    font-size: 0.72rem;
    color: #6E7681 !important;
    font-family: 'JetBrains Mono', monospace !important;
    margin-bottom: 0.5rem;
    padding-left: 0.1rem;
}

/* ── Hero cards (empty state) ────────────────────────────────── */
.hero-card {
    background: #161B22;
    border: 1px solid rgba(48, 54, 61, 0.5);
    border-radius: 8px;
    padding: 1rem;
    height: 100%;
    transition: border-color 0.15s ease, background 0.15s ease;
}
.hero-card:hover {
    border-color: rgba(48, 54, 61, 0.9);
    background: #1A2028;
}
.hero-icon  { font-size: 1.15rem; margin-bottom: 0.4rem; }
.hero-title { font-weight: 600; color: #E6EDF3 !important; font-size: 0.85rem; margin-bottom: 0.2rem; }
.hero-desc  { color: #8B949E !important; font-size: 0.78rem; line-height: 1.5; }

/* ── Chat input ──────────────────────────────────────────────── */
.stChatInput > div {
    border-radius: 8px !important;
    border: 1px solid rgba(48, 54, 61, 0.6) !important;
    background: #161B22 !important;
    transition: border-color 0.15s ease !important;
}
.stChatInput > div:focus-within {
    border-color: rgba(77, 148, 230, 0.5) !important;
    box-shadow: none !important;
}
.stChatInput textarea              { color: #E6EDF3 !important; font-size: 0.86rem !important; }
.stChatInput textarea::placeholder { color: #484F58 !important; }

/* ── Buttons ─────────────────────────────────────────────────── */
.stButton > button {
    background: #21262D !important;
    color: #C9D1D9 !important;
    border: 1px solid rgba(48, 54, 61, 0.7) !important;
    border-radius: 6px !important;
    font-weight: 500 !important;
    font-size: 0.8rem !important;
    transition: all 0.12s ease !important;
    padding: 0.3rem 0.65rem !important;
}
.stButton > button:hover {
    background: #2D333B !important;
    border-color: #484F58 !important;
    color: #E6EDF3 !important;
}

/* ── Download button ─────────────────────────────────────────── */
div[data-testid="stDownloadButton"] > button {
    background: #21262D !important;
    color: #C9D1D9 !important;
    border: 1px solid rgba(48, 54, 61, 0.7) !important;
    border-radius: 6px !important;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
    transition: all 0.12s ease !important;
}
div[data-testid="stDownloadButton"] > button:hover {
    border-color: #484F58 !important;
    background: #2D333B !important;
}

/* ── Expanders ───────────────────────────────────────────────── */
div[data-testid="stExpander"] {
    background: #161B22 !important;
    border: 1px solid rgba(48, 54, 61, 0.5) !important;
    border-radius: 6px !important;
    margin-bottom: 0.4rem !important;
}
div[data-testid="stExpander"] summary {
    font-weight: 600 !important;
    color: #C9D1D9 !important;
    font-size: 0.84rem !important;
}
div[data-testid="stExpander"] summary:hover { color: #E6EDF3 !important; }
div[data-testid="stExpander"] p,
div[data-testid="stExpander"] li { color: #C9D1D9 !important; }

/* ── File uploader ───────────────────────────────────────────── */
div[data-testid="stFileUploader"] {
    border: 1px dashed rgba(48, 54, 61, 0.7) !important;
    border-radius: 6px !important;
    background: #0F1318 !important;
    transition: border-color 0.15s ease !important;
}
div[data-testid="stFileUploader"]:hover { border-color: #484F58 !important; }

/* ── Select boxes ────────────────────────────────────────────── */
div[data-baseweb="select"] > div {
    background: #161B22 !important;
    border-color: rgba(48, 54, 61, 0.6) !important;
    border-radius: 6px !important;
    color: #C9D1D9 !important;
}
div[data-baseweb="select"] > div:hover { border-color: #484F58 !important; }
div[data-baseweb="popover"] {
    background: #161B22 !important;
    border: 1px solid rgba(48, 54, 61, 0.6) !important;
    border-radius: 6px !important;
}

/* ── Toggles ─────────────────────────────────────────────────── */
div[data-testid="stToggle"] label span {
    font-size: 0.82rem !important;
    font-weight: 500 !important;
}

/* ── Radio (horizontal provider selector) ────────────────────── */
div[role="radiogroup"] label {
    font-size: 0.82rem !important;
    font-weight: 500 !important;
}

/* ── Tabs (auth screen) ──────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    background: #161B22;
    border-radius: 6px;
    padding: 3px;
    border: 1px solid rgba(48, 54, 61, 0.5);
}
.stTabs [data-baseweb="tab"] {
    border-radius: 5px !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    color: #8B949E !important;
    padding: 0.35rem 0.9rem !important;
    background: transparent !important;
    border: none !important;
}
.stTabs [aria-selected="true"] {
    background: #21262D !important;
    color: #E6EDF3 !important;
}
.stTabs [data-baseweb="tab-highlight"] { display: none !important; }
.stTabs [data-baseweb="tab-border"] { display: none !important; }

/* ── Text inputs (auth forms) ────────────────────────────────── */
.stTextInput > div > div {
    background: #0F1318 !important;
    border-color: rgba(48, 54, 61, 0.6) !important;
    border-radius: 6px !important;
}
.stTextInput > div > div:focus-within {
    border-color: rgba(77, 148, 230, 0.5) !important;
    box-shadow: none !important;
}
.stTextInput input {
    color: #E6EDF3 !important;
    font-size: 0.85rem !important;
}
.stTextInput input::placeholder { color: #484F58 !important; }
.stTextInput label {
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    color: #8B949E !important;
}

/* ── Form submit button ──────────────────────────────────────── */
.stFormSubmitButton > button {
    background: linear-gradient(135deg, #2563C4 0%, #6E40C9 100%) !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
    font-size: 0.84rem !important;
    padding: 0.45rem 0.9rem !important;
    transition: opacity 0.12s ease !important;
}
.stFormSubmitButton > button:hover { opacity: 0.88 !important; }

/* ── Status widget ───────────────────────────────────────────── */
div[data-testid="stStatusWidget"] {
    background: #161B22 !important;
    border: 1px solid rgba(48, 54, 61, 0.5) !important;
    border-radius: 6px !important;
}

/* ── Misc ────────────────────────────────────────────────────── */
hr { border-color: rgba(48, 54, 61, 0.5) !important; }
.stCaption, [data-testid="stCaptionContainer"] { color: #484F58 !important; font-size: 0.72rem !important; }
.stMarkdown a { color: #4D94E6 !important; text-decoration: none; }
.stMarkdown a:hover { text-decoration: underline; }

/* ── Sidebar branding ────────────────────────────────────────── */
.sb-brand-title {
    font-size: 0.95rem;
    font-weight: 700;
    color: #E6EDF3 !important;
    margin: 0 0 0.05rem 0;
    letter-spacing: -0.01em;
}
.sb-brand-sub {
    font-size: 0.7rem;
    color: #6E7681 !important;
    font-weight: 400;
}
.sb-section {
    font-size: 0.65rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #484F58 !important;
    margin-bottom: 0.35rem;
}

/* ── Auth screen ─────────────────────────────────────────────── */
.auth-wrapper {
    max-width: 400px;
    margin: 2.5rem auto 0 auto;
}
.auth-logo {
    text-align: center;
    margin-bottom: 1.25rem;
}
.auth-logo-icon {
    font-size: 1.8rem;
    background: linear-gradient(135deg, #4D94E6, #8B6DC4);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    display: block;
    line-height: 1;
    margin-bottom: 0.35rem;
}
.auth-logo-title {
    font-size: 1.25rem;
    font-weight: 700;
    color: #E6EDF3 !important;
    letter-spacing: -0.01em;
}
.auth-logo-desc {
    font-size: 0.78rem;
    color: #6E7681 !important;
    margin-top: 0.25rem;
    line-height: 1.5;
}

/* ── User info bar ───────────────────────────────────────────── */
.user-bar {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 0.5rem;
    margin-bottom: 0.4rem;
    font-size: 0.8rem;
    color: #6E7681 !important;
}
.user-bar-name { color: #C9D1D9 !important; font-weight: 500; }

/* ── Hide Streamlit chrome ───────────────────────────────────── */
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
header    { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ─────────── AUTH STATE HELPERS ──────────────────────────────────────────────
def _auth_headers() -> dict:
    """Return Authorization header dict for backend API calls."""
    token = st.session_state.get("token", "")
    return {"Authorization": f"Bearer {token}"} if token else {}


def _is_authenticated() -> bool:
    return bool(st.session_state.get("token"))


def _call_register(name: str, email: str, password: str) -> tuple[bool, str]:
    """Call POST /auth/register. Returns (success, message)."""
    try:
        resp = requests.post(
            f"{API_BASE_URL}/auth/register",
            json={"name": name, "email": email, "password": password},
            timeout=15,
        )
        data = resp.json()
        if resp.status_code == 201:
            st.session_state.token      = data["access_token"]
            st.session_state.user_name  = data["name"]
            st.session_state.user_email = data["email"]
            st.session_state.user_id    = data["user_id"]
            return True, ""
        return False, data.get("detail", "Registration failed.")
    except requests.exceptions.ConnectionError:
        return False, "Cannot reach the backend. Is the server running?"
    except Exception as e:
        return False, f"Unexpected error: {e}"


def _call_login(email: str, password: str) -> tuple[bool, str]:
    """Call POST /auth/login. Returns (success, message)."""
    try:
        resp = requests.post(
            f"{API_BASE_URL}/auth/login",
            json={"email": email, "password": password},
            timeout=15,
        )
        data = resp.json()
        if resp.status_code == 200:
            st.session_state.token      = data["access_token"]
            st.session_state.user_name  = data["name"]
            st.session_state.user_email = data["email"]
            st.session_state.user_id    = data["user_id"]
            return True, ""
        return False, data.get("detail", "Login failed.")
    except requests.exceptions.ConnectionError:
        return False, "Cannot reach the backend. Is the server running?"
    except Exception as e:
        return False, f"Unexpected error: {e}"


def _logout():
    """Clear all auth and chat session state."""
    for key in ["token", "user_name", "user_email", "user_id",
                "messages", "session_id", "ingested_files"]:
        st.session_state.pop(key, None)


# ─────────── LOGIN / SIGNUP SCREEN ───────────────────────────────────────────
def render_auth_screen():
    """Render the unauthenticated login/signup screen."""
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown("""
            <div class="auth-logo">
                <span class="auth-logo-icon">✦</span>
                <div class="auth-logo-title">Agentic Studio</div>
                <div class="auth-logo-desc">
                    RAG &amp; Multi-Tool Research Assistant.<br>
                    Upload documents, search the web, and get structured answers.
                </div>
            </div>
        """, unsafe_allow_html=True)

        login_tab, signup_tab = st.tabs(["Log In", "Sign Up"])

        # ── Log In ──────────────────────────────────────────────────────────
        with login_tab:
            with st.form("login_form", clear_on_submit=False):
                email    = st.text_input("Email", placeholder="you@example.com", key="li_email")
                password = st.text_input("Password", type="password", placeholder="••••••••", key="li_pass")
                submitted = st.form_submit_button("Log In", use_container_width=True)

            if submitted:
                if not email or not password:
                    st.error("Please enter your email and password.")
                else:
                    with st.spinner("Logging in…"):
                        ok, msg = _call_login(email, password)
                    if ok:
                        st.rerun()
                    else:
                        st.error(msg)

        # ── Sign Up ─────────────────────────────────────────────────────────
        with signup_tab:
            with st.form("signup_form", clear_on_submit=False):
                name     = st.text_input("Full Name", placeholder="Your name", key="su_name")
                email    = st.text_input("Email", placeholder="you@example.com", key="su_email")
                password = st.text_input("Password", type="password",
                                         placeholder="Min. 8 characters", key="su_pass")
                submitted = st.form_submit_button("Create Account", use_container_width=True)

            if submitted:
                if not name or not email or not password:
                    st.error("All fields are required.")
                elif len(password) < 8:
                    st.error("Password must be at least 8 characters.")
                else:
                    with st.spinner("Creating your account…"):
                        ok, msg = _call_register(name, email, password)
                    if ok:
                        st.rerun()
                    else:
                        st.error(msg)


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


# ─────────── GATE: SHOW AUTH SCREEN IF NOT LOGGED IN ─────────────────────────
if not _is_authenticated():
    render_auth_screen()
    st.stop()   # Halt execution — nothing below renders for unauthenticated users


# ─────────── SESSION STATE (authenticated users only) ─────────────────────────
# session_id is prefixed with the user's ID to ensure chat history isolation.
# Each user only ever sees their own messages from the DB.
if "messages"       not in st.session_state:
    st.session_state.messages       = []
if "session_id"     not in st.session_state:
    uid_prefix = st.session_state.get("user_id", "")[:8]
    st.session_state.session_id     = f"{uid_prefix}_{uuid.uuid4()}"
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
        <div style="padding:0.4rem 0 0.75rem 0">
            <div class="sb-brand-title">✦ Agentic Studio</div>
            <div class="sb-brand-sub">RAG · Web Search · Memory</div>
        </div>
    """, unsafe_allow_html=True)

    # ── Logged-in user info + logout ─────────────────────────────────────────
    user_name  = st.session_state.get("user_name", "")
    user_email = st.session_state.get("user_email", "")
    st.markdown(
        f'<div style="font-size:0.78rem;color:#484F58 !important;margin-bottom:0.15rem;">Signed in as</div>'
        f'<div style="font-size:0.85rem;font-weight:600;color:#C9D1D9 !important;margin-bottom:0.05rem;">{user_name}</div>'
        f'<div style="font-size:0.73rem;color:#6E7681 !important;margin-bottom:0.6rem;">{user_email}</div>',
        unsafe_allow_html=True,
    )
    if st.button("Log Out", use_container_width=True):
        _logout()
        st.rerun()

    st.markdown("---")
    st.markdown('<div class="sb-section">Model</div>', unsafe_allow_html=True)
    provider = st.radio("Provider", ("Groq", "OpenRouter"), horizontal=True, label_visibility="collapsed")
    MODEL_MAP = {
        "Groq":       ["openai/gpt-oss-120b"],
        "OpenRouter": ["meta-llama/llama-3.1-70b-instruct"],
    }
    selected_model = st.selectbox("Model", MODEL_MAP[provider], label_visibility="collapsed")

    st.markdown("---")
    st.markdown('<div class="sb-section">Engine</div>', unsafe_allow_html=True)
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
            uid_prefix = st.session_state.get("user_id", "")[:8]
            st.session_state.session_id = f"{uid_prefix}_{uuid.uuid4()}"
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
        <span class="app-header-icon">✦</span>
        <div>
            <div class="app-header-title">Agentic Studio</div>
            <div class="app-header-sub">RAG &amp; Multi-Tool Research Assistant</div>
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
        ("⚡", "Smart Routing",   "Automatically picks between RAG, web search, or direct LLM based on your query."),
        ("📚", "RAG Engine",      "Upload PDFs, TXT, or Markdown via the sidebar for grounded, cited answers."),
        ("🌐", "Live Web Search", "Tavily-powered web search for real-time information and summaries."),
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
