# tests/test_summarizer.py
"""
Tests for backend.tools.summarizer — summarize_with_evidence().

Testing strategy:
─────────────────
We mock the OpenAI client (the `client` object in summarizer.py) so no
real API calls are made. This lets us test:

1. The happy path: model returns valid JSON → Pydantic validates it.
2. The repair path: first call returns broken JSON, second call (repair)
   returns valid JSON → the _attempt_repair() mechanism works.
3. The total failure path: both calls return garbage → raw fallback.

WHY mock at `backend.tools.summarizer.client`?
──────────────────────────────────────────────
The module creates `client = OpenAI(...)` at import time. Patching
`backend.tools.summarizer.client` replaces the module-level variable
for the duration of the test, which is exactly what we need.
"""

import json
import pytest
from unittest.mock import patch, MagicMock


VALID_SUMMARY_JSON = {
    "summary": ["Key insight 1", "Key insight 2"],
    "pros_cons": {"pros": ["Fast", "Accurate"], "cons": ["Needs GPU"]},
    "action_items": [{"assignee": "Alice", "task": "Deploy model", "deadline": "2025-10-01"}],
    "citations": ["paper.pdf#chunk:3", "notes.txt#chunk:1"]
}

SAMPLE_CHUNKS = [
    {"source_id": "paper.pdf", "chunk_id": 0, "text": "LLMs are powerful tools.", "score": 0.9},
    {"source_id": "notes.txt", "chunk_id": 1, "text": "RAG improves accuracy.", "score": 0.85},
]


def _make_mock_completion(content: str) -> MagicMock:
    """Build a mock that mimics client.chat.completions.create() return value."""
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock()]
    mock_resp.choices[0].message.content = content
    return mock_resp


class TestSummarizeWithEvidenceHappyPath:
    """Test the normal case where the LLM returns valid JSON."""

    @patch("backend.tools.summarizer.client")
    def test_valid_json_returns_structured_output(self, mock_client):
        """
        When the model returns valid JSON matching the schema,
        summarize_with_evidence should return a validated dict.
        """
        mock_client.chat.completions.create.return_value = _make_mock_completion(
            json.dumps(VALID_SUMMARY_JSON)
        )

        from backend.tools.summarizer import summarize_with_evidence
        result = summarize_with_evidence(SAMPLE_CHUNKS)

        assert "summary" in result
        assert isinstance(result["summary"], list)
        assert len(result["summary"]) == 2
        assert result["summary"][0] == "Key insight 1"

        assert "pros_cons" in result
        assert "pros" in result["pros_cons"]
        assert "cons" in result["pros_cons"]

        assert "action_items" in result
        assert len(result["action_items"]) == 1
        assert result["action_items"][0]["assignee"] == "Alice"

        assert "citations" in result
        assert len(result["citations"]) == 2

    @patch("backend.tools.summarizer.client")
    def test_minimal_valid_json(self, mock_client):
        """
        Even minimal JSON (just summary) should validate when optional
        fields use defaults.
        """
        minimal = {"summary": ["Only one bullet point"]}
        mock_client.chat.completions.create.return_value = _make_mock_completion(
            json.dumps(minimal)
        )

        from backend.tools.summarizer import summarize_with_evidence
        result = summarize_with_evidence(SAMPLE_CHUNKS)

        assert result["summary"] == ["Only one bullet point"]
        # Optional fields should have defaults
        assert result["action_items"] == []
        assert result["citations"] == []


class TestSummarizeRepairPath:
    """
    Test the _attempt_repair() mechanism.

    WHY this path exists:
    LLMs sometimes return JSON with trailing commas, missing quotes,
    or extra commentary. Rather than failing immediately, we make a
    second LLM call asking it to "fix" the broken output. This
    self-healing pattern significantly improves reliability.
    """

    @patch("backend.tools.summarizer.client")
    def test_repair_on_invalid_json(self, mock_client):
        """
        First call returns broken JSON → triggers repair call.
        Second call returns valid JSON → result is usable.
        """
        broken_json = "Here is the summary: {summary: ['bullet 1']}"  # not valid JSON
        valid_json = json.dumps(VALID_SUMMARY_JSON)

        # First call → broken, second call (repair) → valid
        mock_client.chat.completions.create.side_effect = [
            _make_mock_completion(broken_json),
            _make_mock_completion(valid_json),
        ]

        from backend.tools.summarizer import summarize_with_evidence
        result = summarize_with_evidence(SAMPLE_CHUNKS)

        # The repair should have produced a valid result
        assert "summary" in result
        assert result["summary"] == VALID_SUMMARY_JSON["summary"]
        # Verify two calls were made (original + repair)
        assert mock_client.chat.completions.create.call_count == 2

    @patch("backend.tools.summarizer.client")
    def test_repair_with_markdown_wrapped_json(self, mock_client):
        """
        First call returns JSON wrapped in markdown fences.
        json.loads() fails on the fences → triggers repair.
        """
        fenced = f"```json\n{json.dumps(VALID_SUMMARY_JSON)}\n```"

        # First call returns fenced (will fail json.loads), repair returns clean
        mock_client.chat.completions.create.side_effect = [
            _make_mock_completion(fenced),
            _make_mock_completion(json.dumps(VALID_SUMMARY_JSON)),
        ]

        from backend.tools.summarizer import summarize_with_evidence
        result = summarize_with_evidence(SAMPLE_CHUNKS)

        assert "summary" in result


class TestSummarizeTotalFailure:
    """
    Test the fallback when both the original and repair calls fail.

    In this case, summarize_with_evidence returns a dict with 'raw'
    containing the original text — this lets the frontend show
    *something* rather than a blank error screen.
    """

    @patch("backend.tools.summarizer.client")
    def test_complete_failure_returns_raw(self, mock_client):
        """Both calls return garbage → raw fallback."""
        garbage = "I cannot produce JSON right now, sorry."

        mock_client.chat.completions.create.side_effect = [
            _make_mock_completion(garbage),
            _make_mock_completion("Still can't do it."),
        ]

        from backend.tools.summarizer import summarize_with_evidence
        result = summarize_with_evidence(SAMPLE_CHUNKS)

        # Should have 'raw' key with original text or validation error
        assert "raw" in result or "validation_error" in result

    @patch("backend.tools.summarizer.client")
    def test_empty_response_handled(self, mock_client):
        """Empty string from LLM should not crash."""
        mock_client.chat.completions.create.side_effect = [
            _make_mock_completion(""),
            _make_mock_completion(""),
        ]

        from backend.tools.summarizer import summarize_with_evidence
        result = summarize_with_evidence(SAMPLE_CHUNKS)

        # Should not raise — graceful degradation
        assert isinstance(result, dict)
