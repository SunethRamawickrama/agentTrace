from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from agenttrace.api.trace_store import get_all_summaries, get_trace_by_run_id
from agenttrace.graph.builder import build_graph

router = APIRouter()


@router.get("/traces")
def list_traces(
    status: str | None = Query(None),
    task_type: str | None = Query(None),
) -> dict:
    traces = get_all_summaries()
    if status:
        traces = [t for t in traces if t["status"] == status]
    if task_type:
        traces = [t for t in traces if t["taskType"] == task_type]
    return {"traces": traces}


@router.get("/traces/{run_id}")
def get_trace(run_id: str) -> dict:
    raw = get_trace_by_run_id(run_id)
    if raw is None:
        raise HTTPException(status_code=404, detail="Trace not found")
    graph = build_graph(raw)
    return graph.to_svelte_flow()
