#!/usr/bin/env python3
"""
NEXUS Chat REST API Launcher (Root Entry Point)
Delegates to modular backend service in core/api.py.
"""

import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
for _p in (SCRIPT_DIR, os.path.join(SCRIPT_DIR, "core"), os.path.join(SCRIPT_DIR, "agents"), os.path.join(SCRIPT_DIR, "launchers")):
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

from core.api import *

if __name__ == "__main__":
    from core.api import run_server
    host = os.environ.get("NEXUS_HOST", "127.0.0.1")
    port = int(os.environ.get("NEXUS_PORT", "8000"))
    run_server(host=host, port=port)
