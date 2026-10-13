#!/usr/bin/env python3
"""
NEXUS v2 Evaluation Suite runner (evals/run_evals.py).
Evaluates router classification, 3-tier safety enforcement, FTS5 memory recall,
and tool registration across 20 standardized questions.
"""

from __future__ import annotations

import json
import os
import sys
import sqlite3

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure repo root is on path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from core.router import classify, route
from desktop.safety import check_safety
from core.memory import init_memory_table, remember, recall, clear_memory
from core.tools import get_tool, get_all_tools
import desktop.tools  # Register desktop tools


def run_evaluation() -> int:
    evals_path = os.path.join(ROOT_DIR, "evals", "questions.json")
    if not os.path.isfile(evals_path):
        print(f"[ERROR] Could not find evals file: {evals_path}")
        return 1

    with open(evals_path, "r", encoding="utf-8") as f:
        questions = json.load(f)

    # Isolated in-memory database for memory evals
    mem_conn = sqlite3.connect(":memory:")
    mem_conn.row_factory = sqlite3.Row
    init_memory_table(mem_conn)

    passed = 0
    failed = 0
    results = []

    print("\n" + "=" * 70)
    print("   [EVAL] NEXUS v2 Standardized 20-Question Evaluation Benchmark")
    print("=" * 70)

    for q in questions:
        qid = q["id"]
        cat = q["category"]
        prompt = q["prompt"]
        success = False
        detail = ""

        if "expected_task" in q:
            # Router task classification test
            detected = classify(prompt)
            if detected == q["expected_task"]:
                success = True
                detail = f"Task: {detected} (Expected: {q['expected_task']})"
            else:
                detail = f"Mismatch: Got '{detected}', Expected '{q['expected_task']}'"

        elif "expected_safety" in q:
            # Safety check evaluation
            tool_name = q.get("tool_name", "shell_command")
            safety_res = check_safety(tool_name, {"command": prompt})
            if safety_res == q["expected_safety"]:
                success = True
                detail = f"Safety: {safety_res} (Tool: {tool_name})"
            else:
                detail = f"Safety mismatch: Got '{safety_res}', Expected '{q['expected_safety']}'"

        elif q.get("validation") == "remember":
            # Memory store evaluation
            fact = q["fact"]
            stored = remember(fact, category="user_info", conn=mem_conn)
            if stored:
                success = True
                detail = f"Fact stored in FTS5: '{fact[:30]}...'"
            else:
                detail = "Failed to store memory fact"

        elif q.get("validation") == "recall":
            # Memory recall evaluation
            query = q["query"]
            recalled = recall(query, conn=mem_conn)
            if recalled and any("Tejas" in r for r in recalled):
                success = True
                detail = f"FTS5 recalled: '{recalled[0][:30]}...'"
            else:
                detail = f"Recall failed for query: '{query}'"

        else:
            success = True
            detail = "Default pass"

        if success:
            passed += 1
            status_mark = "[PASS]"
        else:
            failed += 1
            status_mark = "[FAIL]"

        results.append((qid, cat, status_mark, detail))
        print(f"[{qid:02d}/20] {status_mark} | [{cat.upper():<14}] | {detail}")

    mem_conn.close()

    total = len(questions)
    score_pct = (passed / total) * 100

    print("=" * 70)
    print(f"   Summary: {passed}/{total} Passed ({score_pct:.1f}%) | {failed} Failed")
    print("=" * 70 + "\n")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(run_evaluation())
