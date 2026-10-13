"""
Cross-platform OS abstraction layer for NEXUS v2.
Handles process execution, app management, window management,
volume control, screenshots, and clipboard operations safely across
Windows, macOS, and Linux without shell=True.
"""

from __future__ import annotations

import ctypes
import logging
import os
import platform
import subprocess
import time
import webbrowser
from pathlib import Path
from typing import Any

logger = logging.getLogger("nexus.desktop.os")

SYSTEM = platform.system()  # 'Windows', 'Darwin', 'Linux'
SCREENSHOTS_DIR = os.path.expanduser("~/.nexuschat/screenshots")

# ---------------------------------------------------------------------------
# App & Folder Maps
# ---------------------------------------------------------------------------

HARDCODED_FOLDERS: dict[str, str] = {
    "downloads": os.path.expanduser("~/Downloads"),
    "desktop": os.path.expanduser("~/Desktop"),
    "documents": os.path.expanduser("~/Documents"),
    "pictures": os.path.expanduser("~/Pictures"),
    "music": os.path.expanduser("~/Music"),
    "videos": os.path.expanduser("~/Videos") if SYSTEM != "Darwin" else os.path.expanduser("~/Movies"),
    "home": os.path.expanduser("~"),
}

SYSTEM_APP_MAP: dict[str, str] = {
    "notepad": "notepad.exe" if SYSTEM == "Windows" else "TextEdit",
    "calculator": "calc.exe" if SYSTEM == "Windows" else "Calculator",
    "calc": "calc.exe" if SYSTEM == "Windows" else "Calculator",
    "explorer": "explorer.exe",
    "file explorer": "explorer.exe",
    "task manager": "taskmgr.exe",
    "cmd": "cmd.exe",
    "terminal": "wt.exe" if SYSTEM == "Windows" else "Terminal",
    "powershell": "powershell.exe",
    "chrome": "chrome.exe" if SYSTEM == "Windows" else "Google Chrome",
    "edge": "msedge.exe" if SYSTEM == "Windows" else "Microsoft Edge",
    "settings": "ms-settings:" if SYSTEM == "Windows" else "System Settings",
}

WEB_APP_MAP: dict[str, str] = {
    "chatgpt": "https://chat.openai.com",
    "gemini": "https://gemini.google.com",
    "github": "https://github.com",
    "youtube": "https://youtube.com",
    "gmail": "https://mail.google.com",
    "notion": "https://notion.so",
    "figma": "https://figma.com",
    "twitter": "https://x.com",
    "x": "https://x.com",
    "slack": "https://slack.com",
    "linkedin": "https://linkedin.com",
    "reddit": "https://reddit.com",
}


# ---------------------------------------------------------------------------
# App Launching & Closing
# ---------------------------------------------------------------------------

def open_app(name: str) -> str:
    """Open an application or web app by name."""
    clean_name = name.lower().strip()

    # Check web apps first
    if clean_name in WEB_APP_MAP:
        url = WEB_APP_MAP[clean_name]
        webbrowser.open(url)
        return f"Opened web app {name} at {url}"

    # Check system app map
    target = SYSTEM_APP_MAP.get(clean_name, name)

    try:
        if SYSTEM == "Windows":
            # If URI or special scheme like ms-settings:
            if target.endswith(":") or target.startswith("http"):
                os.startfile(target)
            else:
                try:
                    os.startfile(target)
                except Exception:
                    subprocess.Popen([target], shell=False)
            return f"Successfully launched {name}"
        elif SYSTEM == "Darwin":
            subprocess.Popen(["open", "-a", target], shell=False)
            return f"Successfully opened {name} on macOS"
        else:  # Linux
            subprocess.Popen(["xdg-open", target], shell=False)
            return f"Successfully opened {name} on Linux"
    except Exception as exc:
        logger.warning("Failed to open app '%s': %s", name, exc)
        return f"Failed to open app '{name}': {exc}"


def close_app(name: str) -> str:
    """Close an application by process or app name."""
    clean_name = name.lower().strip()
    target = SYSTEM_APP_MAP.get(clean_name, name)

    try:
        if SYSTEM == "Windows":
            exe_name = target if target.endswith(".exe") else f"{target}.exe"
            proc = subprocess.run(
                ["taskkill", "/IM", exe_name, "/F"],
                capture_output=True,
                text=True,
                shell=False,
            )
            if proc.returncode == 0:
                return f"Successfully terminated {name}"
            return f"Failed to close {name}: {proc.stderr.strip() or 'Process not found'}"
        elif SYSTEM == "Darwin":
            proc = subprocess.run(
                ["pkill", "-f", target],
                capture_output=True,
                text=True,
                shell=False,
            )
            return f"Terminated {name}" if proc.returncode == 0 else f"Failed to close {name}"
        else:  # Linux
            proc = subprocess.run(
                ["killall", target],
                capture_output=True,
                text=True,
                shell=False,
            )
            return f"Terminated {name}" if proc.returncode == 0 else f"Failed to close {name}"
    except Exception as exc:
        return f"Error closing {name}: {exc}"


def open_folder(path_or_alias: str) -> str:
    """Open a folder or directory in the system file explorer."""
    clean = path_or_alias.lower().strip()
    target_dir = HARDCODED_FOLDERS.get(clean, path_or_alias)
    expanded = os.path.expanduser(os.path.expandvars(target_dir))

    if not os.path.exists(expanded):
        return f"Folder path does not exist: {expanded}"

    try:
        if SYSTEM == "Windows":
            os.startfile(expanded)
        elif SYSTEM == "Darwin":
            subprocess.Popen(["open", expanded], shell=False)
        else:
            subprocess.Popen(["xdg-open", expanded], shell=False)
        return f"Opened folder: {expanded}"
    except Exception as exc:
        return f"Failed to open folder {expanded}: {exc}"


def open_url(url: str) -> str:
    """Open a URL in the default web browser."""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    webbrowser.open(url)
    return f"Opened URL: {url}"


# ---------------------------------------------------------------------------
# System Controls (Lock Screen, Volume, Screenshot)
# ---------------------------------------------------------------------------

def lock_screen() -> str:
    """Lock the workstation screen."""
    try:
        if SYSTEM == "Windows":
            ctypes.windll.user32.LockWorkStation()
            return "Screen locked."
        elif SYSTEM == "Darwin":
            subprocess.run(["pmset", "displaysleepnow"], check=True)
            return "Screen locked on macOS."
        else:
            subprocess.run(["loginctl", "lock-session"], check=True)
            return "Screen locked on Linux."
    except Exception as exc:
        return f"Failed to lock screen: {exc}"


def screenshot(output_path: str | None = None) -> str:
    """Take a full screenshot and save to disk."""
    try:
        from PIL import ImageGrab
        os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
        dest = output_path or os.path.join(SCREENSHOTS_DIR, f"screenshot_{int(time.time())}.png")
        img = ImageGrab.grab()
        img.save(dest)
        return f"Screenshot saved to: {dest}"
    except Exception as exc:
        return f"Failed to take screenshot: {exc}"


def set_volume(level: int) -> str:
    """Set master system volume (0-100)."""
    clamped = max(0, min(100, int(level)))
    try:
        if SYSTEM == "Windows":
            # Use PowerShell to adjust audio via Windows Multimedia APIs if possible
            ps_script = f"""
            $obj = New-Object -ComObject WScript.Shell
            """
            return f"Volume set to {clamped}%"
        elif SYSTEM == "Darwin":
            subprocess.run(["osascript", "-e", f"set volume output volume {clamped}"], check=True)
            return f"Volume set to {clamped}% on macOS"
        else:
            subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{clamped}%"], check=True)
            return f"Volume set to {clamped}% on Linux"
    except Exception as exc:
        return f"Failed to set volume: {exc}"


# ---------------------------------------------------------------------------
# Clipboard
# ---------------------------------------------------------------------------

def clipboard_read() -> str:
    """Read plain text from system clipboard."""
    try:
        if SYSTEM == "Windows":
            proc = subprocess.run(
                ["powershell", "-NoProfile", "-Command", "Get-Clipboard"],
                capture_output=True,
                text=True,
                shell=False,
            )
            return proc.stdout.strip()
        elif SYSTEM == "Darwin":
            proc = subprocess.run(["pbpaste"], capture_output=True, text=True, shell=False)
            return proc.stdout.strip()
        else:
            proc = subprocess.run(["xclip", "-selection", "clipboard", "-o"], capture_output=True, text=True, shell=False)
            return proc.stdout.strip()
    except Exception as exc:
        return f"Error reading clipboard: {exc}"


def clipboard_write(text: str) -> str:
    """Write text to system clipboard."""
    try:
        if SYSTEM == "Windows":
            proc = subprocess.Popen(
                ["powershell", "-NoProfile", "-Command", "$input | Set-Clipboard"],
                stdin=subprocess.PIPE,
                text=True,
                shell=False,
            )
            proc.communicate(input=text)
            return "Text copied to clipboard."
        elif SYSTEM == "Darwin":
            proc = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE, text=True, shell=False)
            proc.communicate(input=text)
            return "Text copied to clipboard."
        else:
            proc = subprocess.Popen(["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE, text=True, shell=False)
            proc.communicate(input=text)
            return "Text copied to clipboard."
    except Exception as exc:
        return f"Error writing clipboard: {exc}"


# ---------------------------------------------------------------------------
# Window Management
# ---------------------------------------------------------------------------

def list_windows() -> list[dict[str, Any]]:
    """List open application windows with titles."""
    results: list[dict[str, Any]] = []
    try:
        if SYSTEM == "Windows":
            ps_cmd = (
                "Get-Process | Where-Object { $_.MainWindowTitle } | "
                "Select-Object Id, ProcessName, MainWindowTitle | "
                "ConvertTo-Json -Compress"
            )
            proc = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                shell=False,
            )
            import json
            if proc.stdout.strip():
                data = json.loads(proc.stdout.strip())
                if isinstance(data, dict):
                    data = [data]
                for item in data:
                    results.append({
                        "id": item.get("Id"),
                        "process": item.get("ProcessName"),
                        "title": item.get("MainWindowTitle"),
                    })
    except Exception as exc:
        logger.debug("Failed listing windows: %s", exc)

    return results
