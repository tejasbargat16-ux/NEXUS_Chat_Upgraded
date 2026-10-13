"""
Three-tier safety system for NEXUS v2 desktop control.
Tiers:
  - SAFE: Auto-executed without prompting (read-only, screenshots, search, apps).
  - CONFIRM: Requires explicit user approval before execution (modifying files, closing apps, shell).
  - REFUSED: Dangerous, destructive, or unauthorized actions that are blocked outright.
"""

from __future__ import annotations

import logging
import re
import secrets
import time
from typing import Any, Literal

logger = logging.getLogger("nexus.desktop.safety")

SafetyTier = Literal["safe", "confirm", "refused"]

SAFE_TOOLS: set[str] = {
    "open_app",
    "open_application",
    "open_website",
    "open_folder",
    "screenshot",
    "take_screenshot",
    "set_volume",
    "web_search",
    "read_file",
    "clipboard_read",
    "read_clipboard",
    "recall_memory",
    "generate_image",
    "list_windows",
}

CONFIRM_TOOLS: set[str] = {
    "close_app",
    "close_application",
    "write_file",
    "delete_file",
    "shell_command",
    "lock_screen",
    "send_keys",
    "clipboard_write",
    "write_clipboard",
}

# Blocklist of irrecoverably destructive shell commands that are always REFUSED
BLOCKED_PATTERNS: list[re.Pattern] = [
    re.compile(r"\brm\s+(-rf?|-fr?)\s+[/~]", re.IGNORECASE),
    re.compile(r"\bformat\s+[a-z]:", re.IGNORECASE),
    re.compile(r"\bdel\s+(/[a-z]\s+)*[c-z]:\\", re.IGNORECASE),
    re.compile(r"\brmdir\s+/s\s+/q\s+[c-z]:\\", re.IGNORECASE),
    re.compile(r"\bmkfs\b", re.IGNORECASE),
    re.compile(r"\bdd\s+if=.*of=/dev/(sd|hd|nvme)", re.IGNORECASE),
    re.compile(r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:", re.IGNORECASE),  # fork bomb
    re.compile(r"\bdrop\s+database\b", re.IGNORECASE),
    re.compile(r">\s*/dev/sda", re.IGNORECASE),
    re.compile(r"\bshutdown\s+(-s|-r|/s|/r)\b", re.IGNORECASE),
]

# Pending confirmations in-memory store
_CONFIRMATIONS: dict[str, dict[str, Any]] = {}


def check_safety(tool_name: str, arguments: dict[str, Any] | None = None) -> SafetyTier:
    """Evaluate whether a tool call is safe, requires confirmation, or is refused."""
    clean_name = tool_name.strip().lower()

    # Check shell command payload against blocked patterns
    if clean_name == "shell_command" and arguments:
        cmd = str(arguments.get("command", ""))
        for pattern in BLOCKED_PATTERNS:
            if pattern.search(cmd):
                logger.warning("Refused dangerous shell command matching %s: %s", pattern.pattern, cmd)
                return "refused"

    if clean_name in SAFE_TOOLS:
        return "safe"

    if clean_name in CONFIRM_TOOLS:
        return "confirm"

    # Default to refused for unknown operations
    return "refused"


def create_confirmation(tool_name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Create a pending confirmation request."""
    conf_id = secrets.token_hex(8)
    record = {
        "id": conf_id,
        "tool_name": tool_name,
        "arguments": arguments,
        "status": "pending",  # 'pending' | 'approved' | 'denied'
        "created_at": time.time(),
        "result": None,
    }
    _CONFIRMATIONS[conf_id] = record
    return record


def get_confirmation(conf_id: str) -> dict[str, Any] | None:
    """Get confirmation record by ID."""
    return _CONFIRMATIONS.get(conf_id)


def get_pending_confirmations() -> list[dict[str, Any]]:
    """Return all pending confirmations."""
    return [c for c in _CONFIRMATIONS.values() if c["status"] == "pending"]


def approve_confirmation(conf_id: str) -> dict[str, Any]:
    """Approve and execute a pending confirmation."""
    rec = _CONFIRMATIONS.get(conf_id)
    if not rec:
        raise KeyError(f"Confirmation '{conf_id}' not found.")
    if rec["status"] != "pending":
        raise ValueError(f"Confirmation '{conf_id}' is already {rec['status']}.")

    rec["status"] = "approved"
    from core.tools import execute_tool
    output = execute_tool(rec["tool_name"], rec["arguments"])
    rec["result"] = output
    return rec


def deny_confirmation(conf_id: str) -> dict[str, Any]:
    """Deny a pending confirmation."""
    rec = _CONFIRMATIONS.get(conf_id)
    if not rec:
        raise KeyError(f"Confirmation '{conf_id}' not found.")
    if rec["status"] != "pending":
        raise ValueError(f"Confirmation '{conf_id}' is already {rec['status']}.")

    rec["status"] = "denied"
    rec["result"] = "Action denied by user."
    return rec


def clear_confirmations() -> None:
    """Clear confirmation store (useful for testing)."""
    _CONFIRMATIONS.clear()
