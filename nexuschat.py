#!/usr/bin/env python3
"""
NEXUS Chat Terminal Launcher (Root Entry Point)
Launches the terminal chat REPL with multi-provider routing and persistent memory.
Delegates to modular CLI in launchers/launch_cli.py.
"""

import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
for _p in (SCRIPT_DIR, os.path.join(SCRIPT_DIR, "core"), os.path.join(SCRIPT_DIR, "agents"), os.path.join(SCRIPT_DIR, "launchers")):
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

from launchers.launch_cli import main

if __name__ == "__main__":
    main()
