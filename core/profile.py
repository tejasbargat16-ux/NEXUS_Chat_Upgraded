"""
Persistent user profile for NEXUS Chat.
Compatibility shim over core.memory.
Stores simple facts about the user so every conversation can be given
context about who it's talking to without repeating every session.
"""

from __future__ import annotations

import os

PROFILE_PATH = os.path.expanduser("~/.nexuschat/profile.txt")


def ensure_dir() -> None:
    os.makedirs(os.path.dirname(PROFILE_PATH), exist_ok=True)


def load_profile() -> str:
    """Return profile facts as newline-separated text."""
    try:
        from core.memory import list_facts
        facts = list_facts(limit=100)
        if facts:
            return "\n".join(f["fact"] for f in facts)
    except Exception:
        pass

    if not os.path.exists(PROFILE_PATH):
        return ""
    with open(PROFILE_PATH, "r", encoding="utf-8") as f:
        return f.read().strip()


def add_fact(fact: str) -> None:
    """Append a new fact to memory."""
    cleaned = fact.strip()
    if not cleaned:
        return

    try:
        from core.memory import remember
        remember(cleaned, category="profile")
    except Exception:
        pass

    ensure_dir()
    with open(PROFILE_PATH, "a", encoding="utf-8") as f:
        f.write(cleaned + "\n")


def clear_profile() -> None:
    """Clear saved facts."""
    try:
        from core.memory import clear_memory
        clear_memory()
    except Exception:
        pass

    ensure_dir()
    with open(PROFILE_PATH, "w", encoding="utf-8") as f:
        f.write("")


def build_system_prompt(base_prompt: str) -> str:
    """Merge the base system prompt with saved profile facts, if any."""
    profile = load_profile()
    if not profile:
        return base_prompt
    return (
        base_prompt
        + "\n\nHere is what you know about the user from previous sessions:\n"
        + profile
    )
