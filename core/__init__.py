"""
NEXUS Core AI & Backend Services
--------------------------------
This package contains the core AI engine, multi-provider routing,
SQLite persistence, identity context, audio and search capabilities.
"""

import os
import sys

# Ensure project root and sibling packages are on sys.path
_CORE_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR = os.path.dirname(_CORE_DIR)
for _p in (_ROOT_DIR, _CORE_DIR, os.path.join(_ROOT_DIR, "agents"), os.path.join(_ROOT_DIR, "launchers")):
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

__all__ = [
    "db",
    "providers",
    "identity",
    "profile",
    "search",
    "imagegen",
    "voice",
    "local_llm",
    "api",
]
