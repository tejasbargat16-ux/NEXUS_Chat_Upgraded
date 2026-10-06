#!/usr/bin/env python3
"""
NEXUS Studio — Master Main Entry Point (main.py)

Connects and orchestrates api.py backend, Desktop App Studio UI, CLI interface,
and Voice Task Assistant.

Usage:
    python main.py                  Launch NEXUS Studio Desktop AI App (Backend + UI)
    python main.py --cli            Run in Terminal CLI mode (nexuschat.py)
    python main.py --server-only    Run API server backend only (api.py)
    python main.py --task           Run dedicated hands-free voice task assistant (Nexus_task.py)
    python main.py --port 8080      Specify custom API port
"""

import os
import sys
import argparse
import threading
import time
import subprocess
import webbrowser

import db
import api

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def launch_browser_desktop(host, port):
    """Launch MS Edge or Chrome in Standalone App Mode for a native desktop application experience."""
    url = f"http://{host}:{port}"
    time.sleep(1.2)  # Wait for Flask server startup
    
    edge_path = os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe")
    chrome_path = os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe")
    chrome_x86 = os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe")
    
    opened = False
    for browser in [edge_path, chrome_path, chrome_x86]:
        if os.path.exists(browser):
            try:
                subprocess.Popen([browser, f"--app={url}", "--title=NEXUS Studio Desktop"])
                opened = True
                print(f"[NEXUS Studio] Opened desktop window via {os.path.basename(browser)}")
                break
            except Exception as e:
                print(f"[NEXUS Studio] App mode launch fallback: {e}")
                
    if not opened:
        print(f"[NEXUS Studio] Opening in default web browser: {url}")
        webbrowser.open(url)


def main():
    parser = argparse.ArgumentParser(description="NEXUS Studio — Master AI Entry Point")
    parser.add_argument("--cli", action="store_true", help="Launch terminal CLI chat mode (nexuschat.py)")
    parser.add_argument("--server-only", action="store_true", help="Launch API backend server only without browser UI")
    parser.add_argument("--task", action="store_true", help="Launch dedicated hands-free voice task assistant (Nexus_task.py)")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host address for API server (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port for API server (default: 8000)")
    args = parser.parse_args()

    # Route 1: Hands-free Voice Task Assistant
    if args.task:
        import Nexus_task as nexus_task
        print("[NEXUS] Launching Voice Task Assistant...")
        nexus_task.main()
        return

    # Route 2: Terminal CLI Mode
    if args.cli:
        import nexuschat
        print("[NEXUS] Launching Terminal CLI Mode...")
        nexuschat.main()
        return

    # Route 3: Server Only Mode
    if args.server_only:
        print(f"[NEXUS] Launching API Server on http://{args.host}:{args.port}...")
        api.run_server(host=args.host, port=args.port)
        return

    # Route 4: Default — Full Desktop Studio (Backend + Desktop UI Window)
    print("==========================================================")
    print("     🚀 NEXUS STUDIO DESKTOP — MASTER LAUNCHER           ")
    print("==========================================================")
    print(f"[NEXUS] Backend API running at http://{args.host}:{args.port}")
    print("[NEXUS] Launching Desktop Studio Window...")
    
    # Launch browser window in background thread
    threading.Thread(
        target=launch_browser_desktop,
        args=(args.host, args.port),
        daemon=True
    ).start()

    # Run API server (blocking main thread)
    api.run_server(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
