#!/usr/bin/env python3
"""
NEXUS Studio Desktop Launcher
Launches the NEXUS Flask backend and opens the Desktop UI in a dedicated, frameless Desktop Window.
"""

import os
import sys
import time
import subprocess
import webbrowser
import threading

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SCRIPT_DIR) if os.path.basename(SCRIPT_DIR) == "launchers" else SCRIPT_DIR
for _p in (ROOT_DIR, os.path.join(ROOT_DIR, "core"), os.path.join(ROOT_DIR, "agents"), SCRIPT_DIR):
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

_server_started = False

def is_server_running(host="127.0.0.1", port=8000):
    """Check if backend is already listening."""
    try:
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            return s.connect_ex((host, port)) == 0
    except Exception:
        return False

def start_backend_server(host="127.0.0.1", port=8000):
    """Import and run the Flask API backend."""
    global _server_started
    if _server_started or is_server_running(host, port):
        return
    _server_started = True
    import api
    api.run_server(host=host, port=port)

def launch_desktop_window(host="127.0.0.1", port=8000):
    """Launch MS Edge or Chrome in App Mode for a native desktop application experience."""
    url = f"http://{host}:{port}"
    time.sleep(1.2) # Give server time to bind port
    
    # Common browser executable paths on Windows
    edge_path = os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe")
    chrome_path = os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe")
    chrome_x86 = os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe")
    
    opened = False
    for browser in [edge_path, chrome_path, chrome_x86]:
        if os.path.exists(browser):
            try:
                subprocess.Popen([browser, f"--app={url}", "--title=NEXUS Studio Desktop"])
                opened = True
                print(f"[NEXUS Desktop] Launched standalone app window via {os.path.basename(browser)}")
                break
            except Exception as e:
                print(f"[NEXUS Desktop] Could not launch app mode: {e}")
                
    if not opened:
        print(f"[NEXUS Desktop] Opening in default web browser: {url}")
        webbrowser.open(url)

def launch_desktop(host="127.0.0.1", port=8000):
    """Callable entry point to launch NEXUS Desktop UI & Server."""
    print("[NEXUS Desktop] Launching NEXUS Studio Desktop UI...")
    # Start server in background thread if not already running
    server_thread = threading.Thread(target=start_backend_server, args=(host, port), daemon=True)
    server_thread.start()
    
    # Launch Desktop app window
    launch_desktop_window(host=host, port=port)

if __name__ == "__main__":
    print("==================================================")
    print("        🚀 NEXUS Studio Desktop Launcher          ")
    print("==================================================")
    launch_desktop()
    # Keep main thread alive when run directly
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[NEXUS Desktop] Shutting down.")
        sys.exit(0)
