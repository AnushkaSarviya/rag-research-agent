# backend/db.py
"""
SQLite persistence layer for chat history.

WHY SQLite over in-memory dict?
─────────────────────────────────
1. Durability   – Data survives server restarts.
2. Concurrency  – WAL mode lets multiple uvicorn workers read/write
                   without blocking each other (readers never block writers).
3. Memory bound – The dict grows unbounded; SQLite keeps data on disk.
4. Pagination   – SQL LIMIT/OFFSET is trivial; doing it on a dict means
                   loading everything into memory first.

WAL (Write-Ahead Logging) mode is critical for FastAPI because the async
event loop may serve concurrent requests. In default journal mode, a writer
blocks all readers. WAL allows concurrent reads + one writer.
"""

import sqlite3
import os
from datetime import datetime, timezone
from typing import List, Tuple

# Store the database inside a `data/` directory at the project root.
# Using a dedicated directory keeps it out of the backend package and
# makes Docker volume-mounting cleaner.
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
DB_PATH = os.path.join(DB_DIR, "chat_history.db")


def get_connection() -> sqlite3.Connection:
    """
    Return a new SQLite connection with WAL mode and foreign keys enabled.

    Each FastAPI request handler runs in its own thread (even with async,
    the default thread pool executor is used for sync endpoints), so we
    open a fresh connection per call rather than sharing one — SQLite
    connections are NOT thread-safe by default.
    """
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")       # concurrent-read friendly
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row                 # dict-like row access
    return conn


def init_db() -> None:
    """
    Create the messages table if it doesn't exist.

    Schema design notes:
    - `id` INTEGER PRIMARY KEY gives us a free auto-increment rowid.
    - `session_id` TEXT is indexed for fast per-session lookups.
    - `role` is 'user' or 'assistant' — keeps the schema close to
       the OpenAI message format, which makes future migrations easier.
    - `created_at` TEXT stores ISO-8601 UTC timestamps; SQLite has no
       native datetime type, but ISO strings sort correctly.
    """
    conn = get_connection()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT    NOT NULL,
                role       TEXT    NOT NULL CHECK(role IN ('user', 'assistant')),
                content    TEXT    NOT NULL,
                created_at TEXT    NOT NULL DEFAULT (datetime('now'))
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_session
            ON messages(session_id, created_at)
        """)
        conn.commit()
    finally:
        conn.close()


def save_message(session_id: str, role: str, content: str) -> None:
    """Insert a single message row."""
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO messages (session_id, role, content, created_at) VALUES (?, ?, ?, ?)",
            (session_id, role, content, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
    finally:
        conn.close()


def get_history(
    session_id: str, limit: int = 50, offset: int = 0
) -> Tuple[List[dict], int]:
    """
    Fetch paginated message history for a session.

    Returns:
        (messages, total_count) where messages is a list of dicts
        with keys: role, content, created_at.

    WHY return total_count alongside the page?
    The frontend needs it to render pagination controls ("Page 2 of 7").
    Doing a COUNT(*) in the same query avoids a second round-trip.
    """
    conn = get_connection()
    try:
        # Total count for pagination metadata
        row = conn.execute(
            "SELECT COUNT(*) AS cnt FROM messages WHERE session_id = ?",
            (session_id,),
        ).fetchone()
        total = row["cnt"]

        rows = conn.execute(
            """
            SELECT role, content, created_at
            FROM messages
            WHERE session_id = ?
            ORDER BY created_at ASC
            LIMIT ? OFFSET ?
            """,
            (session_id, limit, offset),
        ).fetchall()

        messages = [
            {"role": r["role"], "content": r["content"], "created_at": r["created_at"]}
            for r in rows
        ]
        return messages, total
    finally:
        conn.close()


def get_session_messages_as_list(session_id: str) -> List[str]:
    """
    Return all user messages for a session as a flat list of strings.

    This exists for backward compatibility — the agent functions
    (get_response_from_ai_agent, get_response_with_routing) expect
    conversation_history as List[str].
    """
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT content FROM messages
            WHERE session_id = ? AND role = 'user'
            ORDER BY created_at ASC
            """,
            (session_id,),
        ).fetchall()
        return [r["content"] for r in rows]
    finally:
        conn.close()


def delete_history(session_id: str) -> int:
    """
    Delete all messages for a given session_id from SQLite.
    Returns the number of deleted rows.
    """
    conn = get_connection()
    try:
        cursor = conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        conn.commit()
        return cursor.rowcount
    finally:
        conn.close()

