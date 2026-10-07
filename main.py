#!/usr/bin/env python3
"""NEXUS Studio unified application entry point.

All project features are started from this file; the feature code remains in
small modules so it is reusable and testable:

    python main.py                         Desktop Studio (API + browser UI)
    python main.py --server-only           REST API only
    python main.py --cli                   Terminal chat
    python main.py --task                  Hands-free voice task assistant
    python main.py --desktop-command "..." Run one desktop command
    python main.py --check                 Verify the integrated modules load
"""

from __future__ import annotations

import argparse
import importlib
import os
import subprocess
import sys
import threading
import time
import webbrowser
from typing import Iterable

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
for _sub in ("core", "agents", "launchers"):
    _subpath = os.path.join(SCRIPT_DIR, _sub)
    if os.path.isdir(_subpath) and _subpath not in sys.path:
        sys.path.insert(0, _subpath)

# This registry documents the modules connected through the main launcher.
# api.py imports the service modules when the web/Desktop Studio is used.
INTEGRATED_MODULES = (
    "db",
    "providers",
    "profile",
    "identity",
    "agent",
    "search",
    "imagegen",
    "voice",
    "desktop_assistant",
    "api",
    "nexuschat",
    "Nexus_task",
)


def load_module(name: str):
    """Import a project module through one central, clear error path."""
    try:
        return importlib.import_module(name)
    except ImportError as exc:
        raise RuntimeError(
            f"Could not load NEXUS module '{name}': {exc}. "
            "Install the project dependencies with: pip install -r requirements.txt"
        ) from exc


def initialise_storage() -> None:
    """Create the local SQLite schema before a chat/task entry point uses it."""
    load_module("db").init_db()


def launch_browser_desktop(host: str, port: int) -> None:
    """Open the local UI in Edge/Chrome app mode, with a browser fallback."""
    url = f"http://{host}:{port}"
    time.sleep(1.2)

    browser_paths = (
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
    )
    for browser in browser_paths:
        if not os.path.exists(browser):
            continue
        try:
            subprocess.Popen([browser, f"--app={url}", "--title=NEXUS Studio"])
            print(f"[NEXUS] Desktop window opened with {os.path.basename(browser)}")
            return
        except OSError as exc:
            print(f"[NEXUS] Could not launch {os.path.basename(browser)}: {exc}")

    print(f"[NEXUS] Opening in the default browser: {url}")
    webbrowser.open(url)


def check_modules(modules: Iterable[str] = INTEGRATED_MODULES) -> int:
    """Report whether every feature module is importable without starting it."""
    failures = []
    for name in modules:
        try:
            load_module(name)
            print(f"[OK] {name}")
        except RuntimeError as exc:
            failures.append(name)
            print(f"[FAIL] {name}: {exc}")
    return 1 if failures else 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="NEXUS Studio unified launcher")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--cli", action="store_true", help="Run terminal chat (nexuschat.py)")
    mode.add_argument("--server-only", action="store_true", help="Run the REST API without opening a browser")
    mode.add_argument("--task", action="store_true", help="Run the hands-free voice task assistant")
    mode.add_argument("--desktop-command", metavar="TEXT", help="Run one desktop command, then exit")
    mode.add_argument("--check", action="store_true", help="Check that all integrated modules load")
    parser.add_argument("--host", default="127.0.0.1", help="API host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="API port (default: 8000)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.check:
        return check_modules()

    initialise_storage()

    if args.desktop_command:
        desktop = load_module("desktop_assistant")
        handled, message = desktop.handle_desktop_command(args.desktop_command)
        print(message)
        return 0 if handled else 1

    if args.task:
        print("[NEXUS] Launching Voice Task Assistant...")
        load_module("Nexus_task").main()
        return 0

    if args.cli:
        print("[NEXUS] Launching Terminal CLI...")
        load_module("nexuschat").main()
        return 0

    api = load_module("api")
    if args.server_only:
        print(f"[NEXUS] API server: http://{args.host}:{args.port}")
        api.run_server(host=args.host, port=args.port)
        return 0

    print("[NEXUS] Starting Desktop Studio...")
    threading.Thread(
        target=launch_browser_desktop,
        args=(args.host, args.port),
        daemon=True,
    ).start()
    api.run_server(host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n[NEXUS] Stopped.")
        sys.exit(0)
    except RuntimeError as exc:
        print(f"[NEXUS] Startup failed: {exc}", file=sys.stderr)
        sys.exit(1)
