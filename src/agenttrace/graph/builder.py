"""Build a TraceGraph from a raw trace JSON file.

Takes the JSON structure produced by datagen/runner/run_gold.py (with events and
edges lists) and converts it into a typed TraceGraph with TraceNode/TraceEdge
objects, ready for Svelte Flow rendering or Postgres storage.
"""
from __future__ import annotations

import json
from pathlib import Path

from agenttrace.graph.models import (
    NodeStatus,
    NodeType,
    TraceEdge,
    TraceGraph,
    TraceNode,
)


def _classify_node_type(event: dict) -> NodeType:
    event_type = event["event_type"]
    if event_type == "tool_call":
        return NodeType.TOOL_CALL
    if event_type == "message":
        direction = event.get("payload", {}).get("direction", "")
        if direction == "model_error":
            return NodeType.ERROR
        return NodeType.LLM_CALL
    return NodeType.AGENT


def _make_label(event: dict) -> str:
    event_type = event["event_type"]
    agent = event["agent_id"]
    payload = event.get("payload", {})

    if event_type == "state_change":
        phase = payload.get("phase", "")
        return f"{agent} ({phase})"

    if event_type == "tool_call":
        tool = payload.get("tool", agent)
        phase = payload.get("phase", "")
        return f"{tool} ({phase})"

    if event_type == "message":
        direction = payload.get("direction", "")
        if direction == "model_error":
            error_type = payload.get("error_type", "error")
            return f"{agent} ({error_type})"
        return f"{agent} ({direction})"

    return agent


def _parse_status(status: str) -> NodeStatus:
    if status == "failed":
        return NodeStatus.FAILED
    if status == "completed":
        return NodeStatus.COMPLETED
    return NodeStatus.IN_PROGRESS


def _compute_durations(nodes: list[TraceNode]) -> None:
    """Pair up start/end events for agents and tools and compute duration."""
    starts: dict[tuple[str, str], TraceNode] = {}
    for node in nodes:
        agent = node.agent_id
        payload = node.payload
        phase = payload.get("phase", "")
        direction = payload.get("direction", "")

        if phase in ("agent_start", "tool_start") or direction == "model_request":
            starts[(agent, phase or direction)] = node
            continue

        end_key = None
        if phase == "agent_end":
            end_key = (agent, "agent_start")
        elif phase == "tool_end":
            end_key = (agent, "tool_start")
        elif direction == "model_response":
            end_key = (agent, "model_request")

        if end_key and end_key in starts:
            start_node = starts.pop(end_key)
            duration = (node.ts_epoch - start_node.ts_epoch) * 1000
            node.duration_ms = round(duration, 1)
            start_node.duration_ms = round(duration, 1)


def build_graph(trace: dict) -> TraceGraph:
    """Build a TraceGraph from a raw trace dict (as produced by run_gold.py)."""
    events = trace.get("events", [])
    raw_edges = trace.get("edges", [])

    nodes = []
    seen_ids: dict[str, int] = {}
    for event in events:
        raw_id = event["span_id"]
        if raw_id in seen_ids:
            seen_ids[raw_id] += 1
            node_id = f"{raw_id}_{seen_ids[raw_id]}"
        else:
            seen_ids[raw_id] = 0
            node_id = raw_id
        node = TraceNode(
            id=node_id,
            node_type=_classify_node_type(event),
            agent_id=event["agent_id"],
            agent_role=event["agent_role"],
            label=_make_label(event),
            status=_parse_status(event["status"]),
            timestamp=event["timestamp"],
            ts_epoch=event["ts_epoch"],
            payload=event.get("payload", {}),
            component=event.get("component", ""),
            run_id=event.get("run_id", ""),
            task_type=event.get("task_type", ""),
        )
        nodes.append(node)

    _compute_durations(nodes)

    node_ids = {n.id for n in nodes}
    # Map raw span_id to the first node ID using that span (handles deduplication)
    span_to_node: dict[str, str] = {}
    for n in nodes:
        raw = n.id.split("_")[0] if "_" in n.id and n.id.rsplit("_", 1)[-1].isdigit() else n.id
        if raw not in span_to_node:
            span_to_node[raw] = n.id

    edges = []
    seen_edges: set[str] = set()
    for raw_edge in raw_edges:
        source = span_to_node.get(raw_edge["parent_span_id"])
        target = span_to_node.get(raw_edge["child_span_id"])
        if source and target and source in node_ids and target in node_ids:
            edge_id = f"{source}->{target}"
            if edge_id not in seen_edges:
                seen_edges.add(edge_id)
                edges.append(TraceEdge(id=edge_id, source=source, target=target))

    return TraceGraph(
        run_id=trace.get("run_id", ""),
        task_type=trace.get("task_type", ""),
        status=trace.get("status", ""),
        prompt=trace.get("prompt", ""),
        final_output=trace.get("final_output", ""),
        expected=trace.get("expected", ""),
        failure_category=trace.get("failure_category", ""),
        nodes=nodes,
        edges=edges,
    )


def build_graph_from_file(path: str | Path) -> TraceGraph:
    """Load a trace JSON file and build its graph."""
    trace = json.loads(Path(path).read_text())
    return build_graph(trace)
