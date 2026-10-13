"""
Smart task classifier and model router for NEXUS v2.
Classifies user queries into task types (code, study, vision, chat)
and resolves optimal provider fallback chains from config.yaml.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from core.config import get_config, get_route_chain, get_default_chain

logger = logging.getLogger("nexus.router")

# Keyword patterns for rule-based fast classification
CODE_KEYWORDS = {
    "code", "coding", "debug", "debugging", "bug", "error", "traceback",
    "function", "class", "def", "async", "await", "import", "syntax",
    "python", "javascript", "typescript", "c++", "rust", "golang", "java",
    "html", "css", "sql", "git", "bash", "powershell", "api", "endpoint",
    "compile", "exception", "refactor", "unittest", "pytest", "algorithm",
    "regex", "json", "yaml", "frontend", "backend", "docker", "fastapi",
    "quicksort", "sorting", "complexity", "synchronous", "asynchronous",
    "node.js", "nodejs", "react", "vue", "npm", "pip", "database",
}

STUDY_KEYWORDS = {
    "gate", "exam", "syllabus", "concept", "study", "formula", "theorem",
    "math", "mathematics", "calculus", "linear algebra", "physics",
    "electronics", "signals", "circuits", "dsa", "computer organization",
    "operating systems", "dbms", "theory of computation", "compiler design",
    "practice problem", "mock test", "lecture", "textbook", "notes",
    "boolean", "karnaugh", "k-map", "dijkstra", "shortest path", "min-heap",
    "convolution", "lti", "linear time-invariant", "nyquist", "op-amp",
    "eigenvalue", "laplace", "fourier", "fsm",
}

VISION_KEYWORDS = {
    "image", "photo", "picture", "screenshot", "diagram", "draw", "visualize",
    "look at this", "inspect this image", "chart", "graph", "plot",
}


def classify(user_message: str) -> str:
    """Classify the user message into a task category: 'code', 'study', 'vision', or 'chat'.
    
    Fast rule-based classification based on keywords and message characteristics.
    """
    cfg = get_config()
    router_cfg = cfg.get("router", {})
    if router_cfg.get("use_llm", False):
        # Placeholder for LLM classifier if enabled in config
        pass

    text = user_message.lower().strip()

    # Check for image or base64 indicator first
    if "data:image/" in text or any(re.search(rf"\b{re.escape(k)}\b", text) for k in VISION_KEYWORDS):
        return "vision"

    # Count keyword matches for study and code
    study_score = sum(1 for k in STUDY_KEYWORDS if re.search(rf"\b{re.escape(k)}\b", text))
    code_score = sum(1 for k in CODE_KEYWORDS if re.search(rf"\b{re.escape(k)}\b", text))
    if "```" in text:
        code_score += 5

    if study_score > 0 and study_score >= code_score:
        return "study"
    if code_score > 0:
        return "code"
    if study_score > 0:
        return "study"

    return "chat"


def get_chain(task_type: str) -> list[str]:
    """Look up the fallback chain of provider IDs for a given task type."""
    return get_route_chain(task_type)


def route(user_message: str) -> tuple[str, list[str]]:
    """Determine the task type and return the corresponding provider fallback chain.
    
    Returns:
        tuple of (task_type, provider_chain)
    """
    task_type = classify(user_message)
    chain = get_chain(task_type)
    logger.debug("Routed query '%s...' -> task: %s, chain: %s", user_message[:30], task_type, chain)
    return task_type, chain
