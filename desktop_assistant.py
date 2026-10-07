#!/usr/bin/env python3
"""
NEXUS Desktop Assistant (Root Entry Point)
Launches the desktop automation and voice control system.
Delegates to modular engine in agents/desktop_assistant.py.
"""

import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
for _p in (SCRIPT_DIR, os.path.join(SCRIPT_DIR, "core"), os.path.join(SCRIPT_DIR, "agents"), os.path.join(SCRIPT_DIR, "launchers")):
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

from agents.desktop_assistant import *

if __name__ == "__main__":
    from agents.desktop_assistant import main
    main()
