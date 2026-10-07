#!/usr/bin/env python3
"""
NEXUS Voice & Task Assistant (Root Entry Point)
Launches the hands-free voice task assistant.
Delegates to modular engine in agents/Nexus_task.py.
"""

import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
for _p in (SCRIPT_DIR, os.path.join(SCRIPT_DIR, "core"), os.path.join(SCRIPT_DIR, "agents"), os.path.join(SCRIPT_DIR, "launchers")):
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

from agents.Nexus_task import *

if __name__ == "__main__":
    from agents.Nexus_task import main
    main()
