#!/usr/bin/env python3
"""
NEXUS Studio Desktop Launcher (Root Entry Point)
Launches the NEXUS Flask backend and opens the Desktop UI in a dedicated, frameless window.
Delegates to modular launcher in launchers/launch_desktop.py.
"""

import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
for _p in (SCRIPT_DIR, os.path.join(SCRIPT_DIR, "core"), os.path.join(SCRIPT_DIR, "agents"), os.path.join(SCRIPT_DIR, "launchers")):
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

from launchers.launch_desktop import (
    is_server_running,
    start_backend_server,
    launch_desktop_window,
    launch_desktop,
)

if __name__ == "__main__":
    import time
    print("==================================================")
    print("        🚀 NEXUS Studio Desktop Launcher          ")
    print("==================================================")
    launch_desktop()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[NEXUS Desktop] Shutting down.")
        sys.exit(0)
