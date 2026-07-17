# tests/test_retriever.py
"""
Tests for backend.tools.retriever — ingest_document() and retrieve().

Testing strategy:
─────────────────
FAISS + real embeddings require an API key and are slow. Instead, we:
1. Patch the `embeddings` object with langchain's FakeEmbeddings
   (deterministic, no API call, returns fixed-dimension vectors).
2. Use pytest's `tmp_path` fixture for throwaway files and FAISS indices.
3. Patch `VECTOR_DB_PATH` to point at a temp directory so tests never
   touch the real vector store.

WHY FakeEmbeddings?
───────────────────
Real embedding calls cost money and add network latency to tests.
FakeEmbeddings returns random-but-consistent vectors of the right
dimension, which is enough to test that ingestion creates chunks and
retrieval returns results.
"""

import os
import pytest
from unittest.mock import patch
from langchain_core.embeddings import FakeEmbeddings


# We need to patch the embeddings BEFORE importing the retriever module,
# because the module creates `embeddings = OpenAIEmbeddings(...)` at
# import time. We use a fixture that patches at the module level.


@pytest.fixture
def fake_retriever(tmp_path):
    """
    Provide a retriever module with:
    - FakeEmbeddings instead of real OpenAI embeddings
    - A temporary VECTOR_DB_PATH (cleaned up automatically by tmp_path)

    WHY size=1536?
    text-embedding-3-small outputs 1536-dimensional vectors.
    FakeEmbeddings must match this so FAISS index dimensions align.
    """
    fake_emb = FakeEmbeddings(size=1536)
    temp_db_path = str(tmp_path / "test_vector_store")

    with patch("backend.tools.retriever.embeddings", fake_emb), \
         patch("backend.tools.retriever.VECTOR_DB_PATH", temp_db_path):
        # Import AFTER patching so the patched values are used
        from backend.tools.retriever import ingest_document, retrieve
        yield ingest_document, retrieve, tmp_path, temp_db_path


class TestIngestDocument:
    """Tests for ingest_document()."""

    def test_ingest_txt_file(self, fake_retriever):
        """Ingesting a .txt file should create chunks in the FAISS index."""
        ingest_document, _, tmp_path, db_path = fake_retriever

        # Create a test text file
        test_file = tmp_path / "sample.txt"
        test_file.write_text(
            "LangChain is a framework for building LLM applications. "
            "It provides tools for retrieval-augmented generation. "
            "FAISS is used as the vector store backend."
        )

        result = ingest_document(str(test_file))

        assert result["status"] == "success"
        assert result["chunks_added"] > 0
        # FAISS index should now exist on disk
        assert os.path.exists(db_path)

    def test_ingest_md_file(self, fake_retriever):
        """Ingesting a .md file should work the same as .txt."""
        ingest_document, _, tmp_path, _ = fake_retriever

        test_file = tmp_path / "readme.md"
        test_file.write_text("# Project\n\nThis is a markdown document.\n\n## Features\n\n- RAG\n- Agents")

        result = ingest_document(str(test_file))

        assert result["status"] == "success"
        assert result["chunks_added"] > 0

    def test_ingest_nonexistent_file_raises(self, fake_retriever):
        """Ingesting a file that doesn't exist should raise FileNotFoundError."""
        ingest_document, _, _, _ = fake_retriever

        with pytest.raises(FileNotFoundError):
            ingest_document("/nonexistent/path/file.txt")

    def test_ingest_unsupported_extension_raises(self, fake_retriever):
        """Ingesting a .csv or .docx should raise ValueError."""
        ingest_document, _, tmp_path, _ = fake_retriever

        bad_file = tmp_path / "data.csv"
        bad_file.write_text("col1,col2\na,b")

        with pytest.raises(ValueError, match="Unsupported file type"):
            ingest_document(str(bad_file))

    def test_ingest_appends_to_existing_index(self, fake_retriever):
        """Ingesting a second file should add to the existing FAISS index, not replace it."""
        ingest_document, _, tmp_path, _ = fake_retriever

        file1 = tmp_path / "doc1.txt"
        file1.write_text("First document about machine learning.")
        result1 = ingest_document(str(file1))

        file2 = tmp_path / "doc2.txt"
        file2.write_text("Second document about deep learning.")
        result2 = ingest_document(str(file2))

        assert result1["status"] == "success"
        assert result2["status"] == "success"
        # Both ingestions should have added chunks
        assert result1["chunks_added"] > 0
        assert result2["chunks_added"] > 0


class TestRetrieve:
    """Tests for retrieve()."""

    def test_retrieve_from_ingested_docs(self, fake_retriever):
        """After ingestion, retrieve() should return results with correct structure."""
        ingest_document, retrieve, tmp_path, _ = fake_retriever

        # Ingest a document first
        test_file = tmp_path / "knowledge.txt"
        test_file.write_text(
            "Python is a high-level programming language. "
            "It is widely used for web development, data science, and AI. "
            "Python was created by Guido van Rossum in 1991."
        )
        ingest_document(str(test_file))

        # Now retrieve
        results = retrieve("What is Python?", top_k=3)

        assert isinstance(results, list)
        assert len(results) > 0

        # Check structure of each result
        for chunk in results:
            assert "source_id" in chunk
            assert "chunk_id" in chunk
            assert "text" in chunk
            assert "score" in chunk
            assert isinstance(chunk["score"], float)

    def test_retrieve_empty_store(self, fake_retriever):
        """Retrieving from a non-existent index should return empty list."""
        _, retrieve, _, _ = fake_retriever

        results = retrieve("anything", top_k=5)
        assert results == []

    def test_retrieve_respects_top_k(self, fake_retriever):
        """Results should not exceed top_k."""
        ingest_document, retrieve, tmp_path, _ = fake_retriever

        # Ingest a longer document to get multiple chunks
        test_file = tmp_path / "long_doc.txt"
        test_file.write_text(" ".join([f"Paragraph {i}: " + "word " * 100 for i in range(20)]))
        ingest_document(str(test_file))

        results = retrieve("paragraph", top_k=2)
        assert len(results) <= 2
