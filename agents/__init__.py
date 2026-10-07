"""
NEXUS Autonomous Agents & Automation
-----------------------------------
This package contains desktop automation, system command execution,
and autonomous task execution engines.
"""

import os
import sys

_AGENTS_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR = os.path.dirname(_AGENTS_DIR)
for _p in (_ROOT_DIR, _AGENTS_DIR, os.path.join(_ROOT_DIR, "core"), os.path.join(_ROOT_DIR, "launchers")):
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

__all__ = [
    "agent",
    "desktop_assistant",
    "Nexus_task",
]
