"""
NEXUS Launchers
---------------
Entry point scripts for Desktop Studio, Terminal CLI, and Voice Task Assistant.
"""

import os
import sys

_LAUNCHERS_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR = os.path.dirname(_LAUNCHERS_DIR)
for _p in (_ROOT_DIR, _LAUNCHERS_DIR, os.path.join(_ROOT_DIR, "core"), os.path.join(_ROOT_DIR, "agents")):
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)
