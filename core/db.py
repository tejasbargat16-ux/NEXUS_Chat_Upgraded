"""
SQLite persistence layer for NEXUS Chat.
Stores conversations and messages so history survives across sessions.
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.expanduser("~/.nexuschat/history.db")


def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER,
            role TEXT,
            content TEXT,
            created_at TEXT,
            FOREIGN KEY (conversation_id) REFERENCES conversations(id)
        );
        """
    )
    conn.commit()
    conn.close()


def create_conversation(title="New Chat"):
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO conversations (title, created_at) VALUES (?, ?)",
        (title, datetime.now().isoformat()),
    )
    conn.commit()
    conv_id = cur.lastrowid
    conn.close()
    return conv_id


def add_message(conversation_id, role, content):
    conn = get_connection()
    conn.execute(
        "INSERT INTO messages (conversation_id, role, content, created_at) VALUES (?, ?, ?, ?)",
        (conversation_id, role, content, datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def get_messages(conversation_id):
    conn = get_connection()
    rows = conn.execute(
        "SELECT role, content FROM messages WHERE conversation_id = ? ORDER BY id ASC",
        (conversation_id,),
    ).fetchall()
    conn.close()
    return [{"role": r["role"], "content": r["content"]} for r in rows]


def get_conversation(conversation_id):
    conn = get_connection()
    row = conn.execute(
        "SELECT id, title, created_at FROM conversations WHERE id = ?",
        (conversation_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def list_conversations(limit=100):
    conn = get_connection()
    rows = conn.execute(
        "SELECT id, title, created_at FROM conversations ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def rename_conversation(conversation_id, title):
    conn = get_connection()
    conn.execute(
        "UPDATE conversations SET title = ? WHERE id = ?", (title, conversation_id)
    )
    conn.commit()
    conn.close()


def delete_conversation(conversation_id):
    conn = get_connection()
    conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
    conn.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
    conn.commit()
    conn.close()
