from __future__ import annotations

import json
import os
from pathlib import Path

_DEFAULT_DATA_DIR = Path(__file__).resolve().parents[3] / "data" / "traces" / "finance"

_summaries: list[dict] = []
_traces: dict[str, dict] = {}


def load_traces(data_dir: Path | None = None) -> None:
    override = os.getenv("AGENTTRACE_DATA_DIR")
    directory = Path(override) if override else (data_dir or _DEFAULT_DATA_DIR)

    _summaries.clear()
    _traces.clear()

    for path in sorted(directory.glob("*.json")):
        try:
            trace = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            continue

        run_id = trace.get("run_id", "")
        if not run_id:
            continue

        _traces[run_id] = trace
        _summaries.append({
            "runId": run_id,
            "caseId": trace.get("case_id", ""),
            "taskType": trace.get("task_type", ""),
            "status": trace.get("status", ""),
            "prompt": (trace.get("prompt", "") or "")[:200],
        })


def get_all_summaries() -> list[dict]:
    return _summaries


def get_trace_by_run_id(run_id: str) -> dict | None:
    return _traces.get(run_id)
