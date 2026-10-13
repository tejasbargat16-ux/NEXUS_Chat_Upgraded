"""
Long-term memory module for NEXUS v2 using SQLite FTS5.
Stores durable facts about the user and preferences across sessions.
"""

from __future__ import annotations

import json
import logging
import os
import re
import sqlite3
from datetime import datetime
from typing import Any, Callable

logger = logging.getLogger("nexus.memory")

DB_PATH = os.path.expanduser("~/.nexuschat/history.db")


def get_connection(db_path: str | None = None) -> sqlite3.Connection:
    """Return a connection to the SQLite database."""
    target_path = db_path or DB_PATH
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    conn = sqlite3.connect(target_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_memory_table(conn: sqlite3.Connection | None = None) -> None:
    """Create the memory_facts table and FTS5 index if they do not exist."""
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True

    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS memory_facts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fact TEXT NOT NULL UNIQUE,
                category TEXT DEFAULT 'general',
                created_at TEXT NOT NULL,
                source_conversation_id INTEGER
            );

            CREATE VIRTUAL TABLE IF NOT EXISTS memory_facts_fts USING fts5(
                fact,
                category,
                content='memory_facts',
                content_rowid='id'
            );

            CREATE TRIGGER IF NOT EXISTS memory_facts_ai AFTER INSERT ON memory_facts BEGIN
                INSERT INTO memory_facts_fts(rowid, fact, category) VALUES (new.id, new.fact, new.category);
            END;

            CREATE TRIGGER IF NOT EXISTS memory_facts_ad AFTER DELETE ON memory_facts BEGIN
                INSERT INTO memory_facts_fts(memory_facts_fts, rowid, fact, category) VALUES('delete', old.id, old.fact, old.category);
            END;

            CREATE TRIGGER IF NOT EXISTS memory_facts_au AFTER UPDATE ON memory_facts BEGIN
                INSERT INTO memory_facts_fts(memory_facts_fts, rowid, fact, category) VALUES('delete', old.id, old.fact, old.category);
                INSERT INTO memory_facts_fts(rowid, fact, category) VALUES (new.id, new.fact, new.category);
            END;
            """
        )
        conn.commit()
    finally:
        if close_after:
            conn.close()


def _sanitize_fts_query(query: str) -> str:
    """Sanitize user input query into safe FTS5 query tokens."""
    tokens = re.findall(r"\b[a-zA-Z0-9_]{2,}\b", query)
    if not tokens:
        return ""
    # Search each token with prefix matching
    return " OR ".join(f'"{t}"*' for t in tokens)


def remember(
    fact: str,
    category: str = "general",
    conv_id: int | None = None,
    conn: sqlite3.Connection | None = None,
) -> bool:
    """Store a fact in memory with deduplication.
    
    Returns True if stored, False if duplicate.
    """
    cleaned = fact.strip()
    if not cleaned:
        return False

    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True

    try:
        init_memory_table(conn)

        # Check exact duplicate first
        existing = conn.execute(
            "SELECT id FROM memory_facts WHERE lower(fact) = lower(?)",
            (cleaned,),
        ).fetchone()
        if existing:
            return False

        # Check FTS similarity to prevent near-duplicates
        fts_query = _sanitize_fts_query(cleaned)
        if fts_query:
            try:
                similar = conn.execute(
                    """
                    SELECT m.fact
                    FROM memory_facts m
                    JOIN memory_facts_fts f ON m.id = f.rowid
                    WHERE memory_facts_fts MATCH ?
                    LIMIT 3
                    """,
                    (fts_query,),
                ).fetchall()
                for row in similar:
                    # If words overlap heavily (>90%), skip
                    words_new = set(cleaned.lower().split())
                    words_old = set(row["fact"].lower().split())
                    if words_new and words_old:
                        overlap = len(words_new & words_old) / min(len(words_new), len(words_old))
                        if overlap >= 0.9:
                            return False
            except Exception:
                pass

        now = datetime.now().isoformat()
        conn.execute(
            """
            INSERT INTO memory_facts (fact, category, created_at, source_conversation_id)
            VALUES (?, ?, ?, ?)
            """,
            (cleaned, category, now, conv_id),
        )
        conn.commit()
        return True
    finally:
        if close_after:
            conn.close()


def recall(
    query: str,
    limit: int = 5,
    category: str | None = None,
    conn: sqlite3.Connection | None = None,
) -> list[str]:
    """Retrieve relevant facts using FTS5 search. Falls back to recent facts."""
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True

    try:
        init_memory_table(conn)
        fts_q = _sanitize_fts_query(query)
        results: list[str] = []

        if fts_q:
            try:
                if category:
                    rows = conn.execute(
                        """
                        SELECT m.fact
                        FROM memory_facts m
                        JOIN memory_facts_fts f ON m.id = f.rowid
                        WHERE memory_facts_fts MATCH ? AND m.category = ?
                        ORDER BY rank
                        LIMIT ?
                        """,
                        (fts_q, category, limit),
                    ).fetchall()
                else:
                    rows = conn.execute(
                        """
                        SELECT m.fact
                        FROM memory_facts m
                        JOIN memory_facts_fts f ON m.id = f.rowid
                        WHERE memory_facts_fts MATCH ?
                        ORDER BY rank
                        LIMIT ?
                        """,
                        (fts_q, limit),
                    ).fetchall()
                results = [r["fact"] for r in rows]
            except Exception as e:
                logger.debug("FTS search failed (%s), falling back to LIKE", e)

        # Fallback to LIKE if FTS produced nothing
        if not results and query.strip():
            like_term = f"%{query.strip()}%"
            rows = conn.execute(
                """
                SELECT fact FROM memory_facts
                WHERE fact LIKE ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (like_term, limit),
            ).fetchall()
            results = [r["fact"] for r in rows]

        return results
    finally:
        if close_after:
            conn.close()


def list_facts(
    limit: int = 50,
    category: str | None = None,
    conn: sqlite3.Connection | None = None,
) -> list[dict[str, Any]]:
    """List stored memory facts."""
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True

    try:
        init_memory_table(conn)
        if category:
            rows = conn.execute(
                """
                SELECT id, fact, category, created_at, source_conversation_id
                FROM memory_facts
                WHERE category = ?
                ORDER BY id DESC LIMIT ?
                """,
                (category, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                """
                SELECT id, fact, category, created_at, source_conversation_id
                FROM memory_facts
                ORDER BY id DESC LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]
    finally:
        if close_after:
            conn.close()


def delete_fact(fact_id: int, conn: sqlite3.Connection | None = None) -> bool:
    """Delete a fact by its ID."""
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True

    try:
        init_memory_table(conn)
        cur = conn.execute("DELETE FROM memory_facts WHERE id = ?", (fact_id,))
        conn.commit()
        return cur.rowcount > 0
    finally:
        if close_after:
            conn.close()


def clear_memory(conn: sqlite3.Connection | None = None) -> None:
    """Clear all stored facts and FTS records."""
    close_after = False
    if conn is None:
        conn = get_connection()
        close_after = True

    try:
        init_memory_table(conn)
        conn.execute("DELETE FROM memory_facts")
        conn.commit()
    finally:
        if close_after:
            conn.close()


def extract_facts(
    messages: list[dict],
    llm_fn: Callable[[list[dict]], str | dict] | None = None,
) -> list[str]:
    """Extract durable facts about the user from recent conversation messages.
    
    If llm_fn is not provided, uses core.llm.chat_with_fallback.
    """
    if not messages:
        return []

    # Filter to user and assistant messages only
    convo_snippet = []
    for m in messages[-6:]:
        role = m.get("role", "")
        if role in ("user", "assistant"):
            convo_snippet.append(f"{role.upper()}: {m.get('content', '')}")

    if not convo_snippet:
        return []

    prompt = (
        "Extract any durable facts about the user (e.g. preferences, name, projects, tech stack, goals) "
        "revealed in this conversation excerpt. Return ONLY a valid JSON array of strings. "
        "If there are no durable facts about the user, return [].\n\n"
        + "\n".join(convo_snippet)
    )

    try:
        if llm_fn is not None:
            resp = llm_fn([{"role": "user", "content": prompt}])
            text = resp.get("content", "") if isinstance(resp, dict) else str(resp)
        else:
            from core.llm import chat_with_fallback
            from core.config import get_default_chain
            result = chat_with_fallback(
                chain=get_default_chain()[:2],
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
            )
            text = result.get("content", "")

        match = re.search(r"\[.*\]", text, re.DOTALL)
        if match:
            facts = json.loads(match.group(0))
            if isinstance(facts, list):
                return [str(f).strip() for f in facts if str(f).strip()]
    except Exception as e:
        logger.debug("extract_facts failed: %s", e)

    return []
