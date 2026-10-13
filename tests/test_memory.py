"""
Tests for core/memory.py (SQLite FTS5 long-term memory).
"""

import sqlite3
import pytest
from core.memory import (
    init_memory_table,
    remember,
    recall,
    list_facts,
    delete_fact,
    clear_memory,
    extract_facts,
)


@pytest.fixture
def mem_db():
    """Create an isolated in-memory SQLite database with FTS5."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_memory_table(conn)
    yield conn
    conn.close()


def test_remember_and_recall(mem_db):
    stored = remember("User prefers dark mode and Python", category="preferences", conn=mem_db)
    assert stored is True

    # Search by keyword
    results = recall("Python", conn=mem_db)
    assert len(results) == 1
    assert "User prefers dark mode and Python" in results[0]

    # Search with unrelated query
    results_none = recall("quantum chemistry astrophysics", conn=mem_db)
    assert len(results_none) == 0


def test_remember_deduplication(mem_db):
    stored1 = remember("User works at TechCorp", conn=mem_db)
    assert stored1 is True

    # Exact duplicate should not be added
    stored2 = remember("User works at TechCorp", conn=mem_db)
    assert stored2 is False

    facts = list_facts(conn=mem_db)
    assert len(facts) == 1


def test_delete_and_clear_facts(mem_db):
    remember("Fact 1: Likes coffee", conn=mem_db)
    remember("Fact 2: Uses Windows 11", conn=mem_db)

    facts = list_facts(conn=mem_db)
    assert len(facts) == 2

    # Delete fact 1
    deleted = delete_fact(facts[0]["id"], conn=mem_db)
    assert deleted is True

    remaining = list_facts(conn=mem_db)
    assert len(remaining) == 1

    # Clear all
    clear_memory(conn=mem_db)
    assert len(list_facts(conn=mem_db)) == 0


def test_extract_facts_with_mock():
    messages = [
        {"role": "user", "content": "Hi, I am Tejas and I am preparing for the GATE CS exam."},
        {"role": "assistant", "content": "Hello Tejas! I can help you with your GATE prep."},
    ]
    
    mock_llm = lambda msgs: '["User name is Tejas", "User is preparing for GATE CS exam"]'
    extracted = extract_facts(messages, llm_fn=mock_llm)
    assert len(extracted) == 2
    assert "User name is Tejas" in extracted
    assert "User is preparing for GATE CS exam" in extracted
