"""Summarize the harvested finance traces on disk.

Usage: python -m datagen.runner.report
"""
from __future__ import annotations

import json
from collections import Counter

from datagen.finance.utils.utils import TRACES_DIR


def main() -> None:
    files = sorted(p for p in TRACES_DIR.glob("*.json"))
    if not files:
        print(f"no traces in {TRACES_DIR}")
        return

    by_category: Counter[str] = Counter()
    by_task: Counter[str] = Counter()
    passed = 0
    for path in files:
        trace = json.loads(path.read_text())
        by_category[trace["failure_category"]] += 1
        if trace["status"] == "pass":
            passed += 1
        else:
            by_task[trace["task_type"]] += 1

    total = len(files)
    failures = total - passed
    print(f"traces: {total}  passed: {passed}  failures: {failures}")
    print(f"by category: {dict(by_category)}")
    print(f"failures by task_type: {dict(by_task)}")
    print(f"\nusable failure traces for AgentTrace: {failures}")
    if failures < 20:
        print("Below ~20 natural failures — consider enabling fault injection "
              "(see plan step 6) to fill category coverage.")


if __name__ == "__main__":
    main()
