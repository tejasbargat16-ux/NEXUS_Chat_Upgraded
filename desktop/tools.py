"""
Desktop automation tools for NEXUS v2 registered via the core @tool decorator.
Covers app opening/closing, folder navigation, URLs, screen capture,
system volume, clipboard, and safe shell execution.
"""

from __future__ import annotations

import json
import logging
import shlex
import subprocess
from typing import Any

from core.tools import tool
from desktop.os_layer import (
    close_app,
    lock_screen as os_lock_screen,
    open_app,
    open_folder as os_open_folder,
    open_url,
    screenshot as os_screenshot,
    set_volume as os_set_volume,
    clipboard_read as os_clipboard_read,
    clipboard_write as os_clipboard_write,
    list_windows as os_list_windows,
)
from desktop.safety import check_safety

logger = logging.getLogger("nexus.desktop.tools")


@tool(name="open_application", description="Open a desktop application (e.g. notepad, calc, chrome, settings) or web app.")
def tool_open_application(name: str) -> str:
    """Open an application by name."""
    return open_app(name)


@tool(name="close_application", description="Close or terminate a running desktop application by name.")
def tool_close_application(name: str) -> str:
    """Close an application by name."""
    return close_app(name)


@tool(name="open_website", description="Open any website or web URL in the user's default browser.")
def tool_open_website(url: str) -> str:
    """Open a URL in browser."""
    return open_url(url)


@tool(name="open_folder", description="Open a folder in the file manager (e.g. 'downloads', 'desktop', 'documents', or a path).")
def tool_open_folder(path: str) -> str:
    """Open a folder."""
    return os_open_folder(path)


@tool(name="take_screenshot", description="Capture a screenshot of the user's desktop display and save it to disk.")
def tool_take_screenshot() -> str:
    """Capture desktop screenshot."""
    return os_screenshot()


@tool(name="set_volume", description="Set master audio volume level (0 to 100).")
def tool_set_volume(level: int) -> str:
    """Set master system volume."""
    return os_set_volume(level)


@tool(name="lock_screen", description="Lock the computer screen/workstation.")
def tool_lock_screen() -> str:
    """Lock the computer screen."""
    return os_lock_screen()


@tool(name="read_clipboard", description="Read current plain text contents from the system clipboard.")
def tool_read_clipboard() -> str:
    """Read clipboard text."""
    content = os_clipboard_read()
    if not content:
        return "Clipboard is empty."
    return f"Clipboard content:\n{content}"


@tool(name="write_clipboard", description="Copy text to the system clipboard.")
def tool_write_clipboard(text: str) -> str:
    """Write text to clipboard."""
    return os_clipboard_write(text)


@tool(name="list_windows", description="List currently open application windows and their titles.")
def tool_list_windows() -> str:
    """List open windows."""
    windows = os_list_windows()
    if not windows:
        return "No active application windows found."
    lines = ["Active Windows:"]
    for w in windows:
        lines.append(f"- [{w.get('process')}] {w.get('title')} (PID: {w.get('id')})")
    return "\n".join(lines)


@tool(name="shell_command", description="Execute a safe shell command and return stdout/stderr.")
def tool_shell_command(command: str) -> str:
    """Execute a shell command with safety check."""
    safety = check_safety("shell_command", {"command": command})
    if safety == "refused":
        return f"Refused: The command '{command}' contains unsafe or destructive operations and cannot be executed."

    try:
        # Split command safely without shell=True
        args = shlex.split(command, posix=False) if subprocess.os.name == "nt" else shlex.split(command)
        proc = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=30,
            shell=False,
        )
        output = proc.stdout
        if proc.stderr:
            output += f"\n[stderr]: {proc.stderr}"
        return output.strip() or f"Command exited with code {proc.returncode}"
    except subprocess.TimeoutExpired:
        return "Command timed out after 30 seconds."
    except Exception as exc:
        return f"Execution error: {exc}"
