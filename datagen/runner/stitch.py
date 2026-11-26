"""Stitch per-component trace fragments into one canonical trace.

Correlation is by time window (the runner executes runs sequentially, so every
fragment event in a run's window belongs to that run) plus component/agent name
for the cross-process parent link (orchestrator delegation span -> specialist root).
"""
from __future__ import annotations

import json

from datagen.finance.utils.utils import FRAGMENTS_DIR


def read_window(start: float, end: float) -> list[dict]:
    """Read all fragment events whose ts_epoch falls in [start, end]."""
    events: list[dict] = []
    for path in FRAGMENTS_DIR.glob("*.jsonl"):
        with path.open() as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                e = json.loads(line)
                if start <= e.get("ts_epoch", 0) <= end:
                    events.append(e)
    return events


def _is_agent_start(e: dict) -> bool:
    return e["event_type"] == "state_change" and e["payload"].get("phase") == "agent_start"


def stitch(fragment_events: list[dict], run_id: str, task_type: str) -> tuple[list[dict], list[dict]]:
    """Return (canonical_events, edges). Pure — safe to unit test with synthetic input."""
    events = sorted(fragment_events, key=lambda e: (e.get("ts_epoch", 0), e.get("seq", 0)))

    # Orchestrator's delegation spans: agent_start for a sub-agent (a specialist).
    delegation: dict[str, str] = {}
    for e in events:
        if e["component"] == "orchestrator" and _is_agent_start(e) and e["agent_id"] != "orchestrator":
            delegation.setdefault(e["agent_id"], e["span_id"])

    out: list[dict] = []
    for e in events:
        ev = dict(e)
        ev["run_id"] = run_id
        ev["task_type"] = task_type
        # Link a specialist process's root agent span to the orchestrator's
        # delegation span for that specialist.
        if (e["component"] != "orchestrator" and e["parent_span_id"] is None
                and _is_agent_start(e) and e["agent_id"] == e["component"]):
            ev["parent_span_id"] = delegation.get(e["agent_id"])
        out.append(ev)

    seen = set()
    edges = []
    for ev in out:
        parent = ev["parent_span_id"]
        if parent and (parent, ev["span_id"]) not in seen:
            seen.add((parent, ev["span_id"]))
            edges.append({"parent_span_id": parent, "child_span_id": ev["span_id"]})
    return out, edges
