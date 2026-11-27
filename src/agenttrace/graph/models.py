"""Graph data structures for agent trace visualization.

These models represent a single run's execution as a directed acyclic graph.
Each node is an agent step (agent lifecycle, LLM call, or tool call) and each
edge is a parent-child relationship between steps. The structures carry all the
information needed to render a Svelte Flow graph on the frontend.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class NodeType(str, Enum):
    AGENT = "agent"
    LLM_CALL = "llm_call"
    TOOL_CALL = "tool_call"
    ERROR = "error"


class NodeStatus(str, Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TraceNode:
    id: str
    node_type: NodeType
    agent_id: str
    agent_role: str
    label: str
    status: NodeStatus
    timestamp: str
    ts_epoch: float
    payload: dict = field(default_factory=dict)
    component: str = ""
    run_id: str = ""
    task_type: str = ""
    duration_ms: float | None = None


@dataclass
class TraceEdge:
    id: str
    source: str
    target: str


@dataclass
class TraceGraph:
    run_id: str
    task_type: str
    status: str
    prompt: str
    final_output: str
    expected: str | float | dict | list
    failure_category: str
    nodes: list[TraceNode] = field(default_factory=list)
    edges: list[TraceEdge] = field(default_factory=list)

    def to_svelte_flow(self) -> dict:
        """Convert to a dict with 'nodes' and 'edges' matching Svelte Flow's
        Node[] and Edge[] shape, ready to be serialized as JSON for the frontend."""
        y_spacing = 120
        x_offset_by_component = {"orchestrator": 0}
        component_idx = 1

        sf_nodes = []
        for i, node in enumerate(self.nodes):
            if node.component not in x_offset_by_component:
                x_offset_by_component[node.component] = component_idx * 350
                component_idx += 1

            x = x_offset_by_component.get(node.component, 0)
            y = i * y_spacing

            sf_nodes.append({
                "id": node.id,
                "type": node.node_type.value,
                "position": {"x": x, "y": y},
                "data": {
                    "label": node.label,
                    "agentId": node.agent_id,
                    "agentRole": node.agent_role,
                    "status": node.status.value,
                    "nodeType": node.node_type.value,
                    "timestamp": node.timestamp,
                    "durationMs": node.duration_ms,
                    "payload": node.payload,
                    "component": node.component,
                    "taskType": node.task_type,
                },
            })

        edge_style = "stroke:#D2D2D2; stroke-width:2;"
        sf_edges = []
        for edge in self.edges:
            sf_edges.append({
                "id": edge.id,
                "source": edge.source,
                "target": edge.target,
                "style": edge_style,
                "animated": True,
            })

        return {
            "runId": self.run_id,
            "taskType": self.task_type,
            "status": self.status,
            "prompt": self.prompt,
            "finalOutput": self.final_output,
            "expected": self.expected,
            "failureCategory": self.failure_category,
            "nodes": sf_nodes,
            "edges": sf_edges,
        }
