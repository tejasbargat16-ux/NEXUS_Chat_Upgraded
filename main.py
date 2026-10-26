#!/usr/bin/env python3
"""NEXUS Studio unified application entry point.

All project features are started from this file; the feature code remains in
small modules so it is reusable and testable:

    python main.py                         Desktop Studio (Native Window / HUD)
    python main.py --browser               Browser-only mode
    python main.py --server-only           REST API only
    python main.py --cli                   Terminal chat (launch_cli)
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
for _sub in ("core", "agents", "launchers", "desktop"):
    _subpath = os.path.join(SCRIPT_DIR, _sub)
    if os.path.isdir(_subpath) and _subpath not in sys.path:
        sys.path.insert(0, _subpath)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

INTEGRATED_MODULES = (
    "core.db",
    "core.llm",
    "core.agent",
    "core.tools",
    "core.memory",
    "core.router",
    "core.providers",
    "core.profile",
    "core.identity",
    "core.search",
    "core.imagegen",
    "core.voice",
    "desktop.os_layer",
    "desktop.safety",
    "desktop.tools",
    "launchers.launch_cli",
    "launchers.launch_task",
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
    load_module("core.db").init_db()


def launch_browser_desktop(host: str, port: int) -> None:
    """Open the local UI in Edge/Chrome app mode, with a browser fallback."""
    url = f"http://{host}:{port}"
    time.sleep(1.2)

    browser_paths = (
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
    )
    for browser in browser_paths:
        if not os.path.exists(browser):
            continue
        try:
            subprocess.Popen([browser, f"--app={url}", "--title=NEXUS Studio"], shell=False)
            print(f"[NEXUS] Desktop window opened with {os.path.basename(browser)}")
            return
        except OSError as exc:
            print(f"[NEXUS] Could not launch {os.path.basename(browser)}: {exc}")

    print(f"[NEXUS] Opening in default browser: {url}")
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
    parser = argparse.ArgumentParser(description="NEXUS v2 unified launcher")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--cli", action="store_true", help="Run terminal chat")
    mode.add_argument("--server-only", action="store_true", help="Run REST API without UI window")
    mode.add_argument("--browser", action="store_true", help="Launch UI in default browser instead of native window")
    mode.add_argument("--task", action="store_true", help="Run the hands-free voice task assistant")
    mode.add_argument("--desktop-command", metavar="TEXT", help="Run one desktop command, then exit")
    mode.add_argument("--check", action="store_true", help="Check that all integrated modules load")
    parser.add_argument("--host", default="127.0.0.1", help="API host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=5000, help="API port (default: 5000)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.check:
        return check_modules()

    initialise_storage()

    if args.desktop_command:
        desktop = load_module("agents.desktop_assistant")
        handled, message = desktop.handle_desktop_command(args.desktop_command)
        print(message)
        return 0 if handled else 1

    if args.task:
        print("[NEXUS] Launching Voice Task Assistant...")
        load_module("launchers.launch_task").main()
        return 0

    if args.cli:
        print("[NEXUS] Launching Terminal CLI...")
        load_module("launchers.launch_cli").main()
        return 0

    api_mod = load_module("desktop.api")

    if args.server_only:
        print(f"[NEXUS] API server running at http://{args.host}:{args.port}")
        api_mod.run_server(host=args.host, port=args.port)
        return 0

    # Start API server in background daemon thread
    server_thread = threading.Thread(
        target=api_mod.run_server,
        kwargs={"host": args.host, "port": args.port},
        daemon=True,
    )
    server_thread.start()
    time.sleep(1.0)

    url = f"http://{args.host}:{args.port}"

    if args.browser:
        print(f"[NEXUS] Opening browser at {url}...")
        webbrowser.open(url)
        server_thread.join()
        return 0

    # Attempt native window UI via pywebview (only on Python versions where pythonnet is stable)
    if sys.version_info < (3, 14):
        try:
            print(f"[NEXUS] Starting native desktop window UI at {url}...")
            ui_mod = load_module("desktop.ui")
            ui_mod.launch_ui(url=url)
            return 0
        except Exception as exc:
            print(f"[NEXUS] pywebview native UI unavailable ({exc}), falling back to desktop window...")

    print(f"[NEXUS] Launching desktop app window at {url}...")
    launch_browser_desktop(args.host, args.port)
    server_thread.join()
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
