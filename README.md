# Agentic Chatbot FastAPI

A Research & Summarization Agent built with FastAPI, LangGraph, and Streamlit. Features RAG (Retrieval-Augmented Generation) capabilities with document ingestion, vector search, and structured summarization.

## Features

- 🤖 **Multi-Provider LLM Support**: Groq and OpenRouter
- 📚 **RAG Capabilities**: Document ingestion and retrieval using FAISS vector store
- 📝 **Structured Summarization**: Generate summaries with pros/cons, action items, and citations
- 💬 **Conversation History**: Session-based chat history tracking
- 🎨 **Modern UI**: Streamlit-based frontend

## Project Structure

```
Agentic_Chatbot_FastAPI/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── ai_agent.py          # LangGraph agent with RAG tool
│   ├── config.py            # Configuration settings
│   └── tools/
│       ├── retriever.py     # FAISS vector store operations
│       └── summarizer.py   # Structured summarization
├── frontend.py              # Streamlit UI
└── env.example              # Environment variables template
```

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd Agentic_Chatbot_FastAPI
```

### 2. Create Virtual Environment

```bash
python -m venv .venv

# On Windows
.venv\Scripts\activate

# On macOS/Linux
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install fastapi uvicorn streamlit langchain-groq langchain-openai langchain-community langgraph faiss-cpu python-dotenv pydantic openai
```

### 4. Configure Environment Variables

**IMPORTANT**: Never commit your `.env` file to version control!

1. Copy the example environment file:
   ```bash
   cp env.example .env
   ```

2. Edit `.env` and add your API keys:
   ```env
   GROQ_API_KEY=your_actual_groq_key
   OPEN_ROUTER_API_KEY=your_actual_openrouter_key
   TAVILY_API_KEY=your_actual_tavily_key  # Optional
   ```

### 5. Run the Application

**Start the Backend:**
```bash
cd backend
python main.py
```
The API will be available at `http://127.0.0.1:9999`

**Start the Frontend (in a new terminal):**
```bash
streamlit run frontend.py
```

## API Endpoints

- `POST /chat` - Chat with the agent
- `GET /history/{session_id}` - Get chat history
- `GET /models` - List available models
- `GET /health` - Health check
- `POST /ingest` - Ingest documents into vector store

## Security Best Practices

✅ **DO:**
- Use environment variables for all API keys
- Keep `.env` file in `.gitignore`
- Use `env.example` as a template
- Review commits before pushing to ensure no secrets are included

❌ **DON'T:**
- Commit `.env` files
- Hardcode API keys in source code
- Share API keys in screenshots or documentation
- Push sensitive data to public repositories

## Getting API Keys

- **Groq**: https://console.groq.com/
- **OpenRouter**: https://openrouter.ai/
- **Tavily**: https://tavily.com/ (optional)

## License

MIT

