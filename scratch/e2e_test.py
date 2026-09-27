import requests
import time
import os

BASE_URL = "http://127.0.0.1:9999"

def check(name, cond):
    if cond:
        print(f"PASS: {name}")
    else:
        print(f"FAIL: {name}")

def test_all():
    # 1. Health
    r = requests.get(f"{BASE_URL}/health")
    check("/health works", r.status_code == 200 and r.json().get("status") == "ok")

    # 2. Docs
    r = requests.get(f"{BASE_URL}/docs")
    check("/docs works", r.status_code == 200)

    # 3. Invalid route
    r = requests.get(f"{BASE_URL}/does_not_exist")
    check("Invalid route returns error", r.status_code == 404)

    # 4. Auth
    email = f"test_{int(time.time())}@example.com"
    r = requests.post(f"{BASE_URL}/auth/register", json={"name": "Test User", "email": email, "password": "password123"})
    check("Register works", r.status_code == 201)
    token = r.json()["access_token"]
    user_id = r.json()["user_id"]

    r = requests.post(f"{BASE_URL}/auth/login", json={"email": email, "password": "password123"})
    check("Login works", r.status_code == 200)

    # 5. Invalid File validation
    r = requests.post(f"{BASE_URL}/ingest", files={"file": ("test.xyz", b"hello", "text/plain")})
    check("File validation works (.xyz rejected)", r.status_code == 400)

    # 6. Valid File Ingestion
    r = requests.post(f"{BASE_URL}/ingest", files={"file": ("test.txt", b"The secret code for the vault is 8844.", "text/plain")})
    check("RAG ingestion works (.txt)", r.status_code == 200 and r.json().get("status") == "success")

    # 7. Chat (General/No Tool)
    payload = {
        "model_name": "openai/gpt-oss-120b",
        "model_provider": "Groq",
        "system_prompt": "",
        "messages": ["Hi there!"],
        "allow_search": False,
        "use_tool_routing": True,
        "session_id": f"sess_{user_id}"
    }
    r = requests.post(f"{BASE_URL}/chat", json=payload)
    if r.status_code == 200:
        data = r.json()
        tool = data.get("tool_decision", {}).get("tool")
        check("Chat (no tool) works", tool == "no_tool")
    else:
        check("Chat (no tool) failed", False)

    # 8. Chat (RAG)
    payload["messages"] = ["Hi there!", "What is the secret code for the vault?"]
    r = requests.post(f"{BASE_URL}/chat", json=payload)
    if r.status_code == 200:
        data = r.json()
        tool = data.get("tool_decision", {}).get("tool")
        ans = data.get("summary", [""])[0]
        check("Chat (RAG tool) selected", tool == "research_tool")
        check("RAG answers are grounded", "8844" in ans)
    else:
        check("Chat (RAG) failed", False)

    # 9. Out-of-context RAG
    payload["messages"] = ["What is the capital of Mars according to the documents?"]
    r = requests.post(f"{BASE_URL}/chat", json=payload)
    if r.status_code == 200:
        data = r.json()
        tool = data.get("tool_decision", {}).get("tool")
        ans = data.get("summary", [""])[0]
        check("Out-of-context question handled safely", "not available" in ans.lower() or "not mention" in ans.lower() or "unknown" in ans.lower())
    else:
        check("Out-of-context RAG failed", False)

    # 10. Web Search
    payload["messages"] = ["What is the weather in Tokyo right now?"]
    payload["allow_search"] = True
    r = requests.post(f"{BASE_URL}/chat", json=payload)
    if r.status_code == 200:
        data = r.json()
        tool = data.get("tool_decision", {}).get("tool")
        check("Web search selected", tool == "web_search")
    else:
        check("Web search failed", False)

    # 11. History persistence
    r = requests.get(f"{BASE_URL}/history/sess_{user_id}")
    check("Chat history persists", r.status_code == 200 and len(r.json().get("history", [])) > 0)


if __name__ == "__main__":
    try:
        test_all()
    except Exception as e:
        print(f"Error: {e}")
