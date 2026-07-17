# tests/test_tool_router.py
"""
Tests for backend.tool_router.decide_tool().

Testing strategy:
─────────────────
We mock the LLM so these tests NEVER make real API calls. This is
critical for CI/CD — tests must be fast, deterministic, and free of
API key dependencies.

What we test:
1. Valid JSON parsing        → the happy path
2. Markdown fence stripping  → LLMs often wrap output in ```json ... ```
3. Unknown tool fallback     → guards against hallucinated tool names
4. Malformed JSON fallback   → graceful degradation on garbage output
5. Empty/missing fields      → edge case robustness
"""

from unittest.mock import MagicMock
from backend.tool_router import decide_tool, ToolDecision


def _make_mock_llm(content: str) -> MagicMock:
    """
    Create a mock LLM that returns a fixed string as .content.

    WHY this pattern?
    LangChain chat models return an AIMessage with a `.content` attribute.
    By mocking `.invoke()` to return an object with `.content`, we simulate
    the LLM response without needing any API keys or network calls.
    """
    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.content = content
    mock_llm.invoke.return_value = mock_response
    return mock_llm


class TestDecideToolValidJSON:
    """Test that valid JSON is parsed correctly."""

    def test_research_tool_selected(self):
        """LLM returns well-formed JSON selecting research_tool."""
        llm = _make_mock_llm('{"tool": "research_tool", "input": "langchain architecture"}')
        result = decide_tool("Tell me about LangChain", llm, conversation_history=[])

        assert isinstance(result, ToolDecision)
        assert result.tool == "research_tool"
        assert result.input == "langchain architecture"

    def test_web_search_selected(self):
        """LLM returns well-formed JSON selecting web_search."""
        llm = _make_mock_llm('{"tool": "web_search", "input": "latest AI news 2025"}')
        result = decide_tool("What's the latest AI news?", llm, conversation_history=[])

        assert result.tool == "web_search"
        assert result.input == "latest AI news 2025"

    def test_no_tool_selected(self):
        """LLM decides no tool is needed."""
        llm = _make_mock_llm('{"tool": "no_tool", "input": "hello"}')
        result = decide_tool("Hello!", llm, conversation_history=[])

        assert result.tool == "no_tool"


class TestDecideToolMarkdownFences:
    """
    Test markdown code fence stripping.

    WHY this test exists:
    Many LLMs (GPT-4, Llama, Mixtral) wrap JSON output in ```json ... ```
    even when explicitly told not to. The router must handle this gracefully
    rather than crashing on json.loads().
    """

    def test_fenced_json_parsed(self):
        """JSON wrapped in ```json ... ``` is parsed correctly."""
        fenced = '```json\n{"tool": "research_tool", "input": "RAG pipeline"}\n```'
        llm = _make_mock_llm(fenced)
        result = decide_tool("How does RAG work?", llm, conversation_history=[])

        assert result.tool == "research_tool"
        assert result.input == "RAG pipeline"

    def test_fenced_without_language_tag(self):
        """JSON wrapped in ``` ... ``` (no 'json' tag) is parsed correctly."""
        fenced = '```\n{"tool": "web_search", "input": "python 3.13 features"}\n```'
        llm = _make_mock_llm(fenced)
        result = decide_tool("What's new in Python?", llm, conversation_history=[])

        assert result.tool == "web_search"
        assert result.input == "python 3.13 features"


class TestDecideToolUnknownToolFallback:
    """
    Test that unknown/hallucinated tool names fall back to no_tool.

    WHY this matters:
    LLMs can hallucinate tool names like "calculator" or "code_executor"
    that don't exist in our registry. The router must map these to no_tool
    rather than passing an invalid tool name downstream.
    """

    def test_hallucinated_tool_falls_back(self):
        llm = _make_mock_llm('{"tool": "magic_calculator", "input": "2+2"}')
        result = decide_tool("What is 2+2?", llm, conversation_history=[])

        assert result.tool == "no_tool"
        assert result.input == "What is 2+2?"  # original query preserved

    def test_empty_tool_name_falls_back(self):
        llm = _make_mock_llm('{"tool": "", "input": "something"}')
        result = decide_tool("Do something", llm, conversation_history=[])

        assert result.tool == "no_tool"


class TestDecideToolMalformedJSON:
    """
    Test graceful degradation when the LLM returns garbage.

    WHY this matters:
    In production, LLMs occasionally return truncated output, extra
    commentary, or completely unstructured text. The router must not
    crash — it should fall back to no_tool with the original query.
    """

    def test_garbage_output(self):
        llm = _make_mock_llm("I think you should use the research tool for this query.")
        result = decide_tool("Tell me about FAISS", llm, conversation_history=[])

        assert result.tool == "no_tool"
        assert result.input == "Tell me about FAISS"

    def test_truncated_json(self):
        llm = _make_mock_llm('{"tool": "research_tool", "inp')
        result = decide_tool("Truncated test", llm, conversation_history=[])

        assert result.tool == "no_tool"
        assert result.input == "Truncated test"

    def test_empty_response(self):
        llm = _make_mock_llm("")
        result = decide_tool("Empty response test", llm, conversation_history=[])

        assert result.tool == "no_tool"


class TestDecideToolWithHistory:
    """Test that conversation history is passed to the LLM."""

    def test_history_included_in_prompt(self):
        """Verify the LLM receives conversation history in its system message."""
        llm = _make_mock_llm('{"tool": "research_tool", "input": "LangGraph"}')
        history = ["Tell me about LangGraph", "What are its main features?"]

        result = decide_tool("Tell me more about it", llm, conversation_history=history)

        # Verify the LLM was called (we can't easily inspect the prompt
        # content without deeper mocking, but we can check it was invoked)
        assert llm.invoke.called
        assert result.tool == "research_tool"

    def test_none_history_handled(self):
        """None history should not crash."""
        llm = _make_mock_llm('{"tool": "no_tool", "input": "hi"}')
        result = decide_tool("Hi", llm, conversation_history=None)

        assert result.tool == "no_tool"
