"""
Persistent user profile for NEXUS Chat.
Stores simple facts about the user in a plain text file so every
conversation can be given context about who it's talking to, without
the user having to repeat themselves each session.
"""

import os

PROFILE_PATH = os.path.expanduser("~/.nexuschat/profile.txt")


def ensure_dir():
    os.makedirs(os.path.dirname(PROFILE_PATH), exist_ok=True)


def load_profile():
    """Return the profile text, or '' if nothing saved yet."""
    if not os.path.exists(PROFILE_PATH):
        return ""
    with open(PROFILE_PATH, "r") as f:
        return f.read().strip()


def add_fact(fact):
    """Append a new fact as its own line."""
    ensure_dir()
    with open(PROFILE_PATH, "a") as f:
        f.write(fact.strip() + "\n")


def clear_profile():
    ensure_dir()
    with open(PROFILE_PATH, "w") as f:
        f.write("")


def build_system_prompt(base_prompt):
    """Merge the base system prompt with saved profile facts, if any."""
    profile = load_profile()
    if not profile:
        return base_prompt
    return (
        base_prompt
        + "\n\nHere is what you know about the user from previous sessions:\n"
        + profile
    )
