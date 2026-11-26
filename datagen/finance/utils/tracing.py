"""Trace capture via ADK callbacks (no OpenTelemetry).

Each process (the orchestrator, and each specialist A2A server) owns one
``TraceCollector`` that appends canonical trace events to a per-component JSONL
fragment file under ``data/traces/finance/_fragments/``. The runner stitches the
fragments from all components into one trace per run, correlating cross-process
events by time window (runs execute sequentially) — see runner/run_gold.py.

Canonical event shape (README "Canonical trace event"):
    run_id, span_id, parent_span_id, agent_id, agent_role, task_type,
    event_type ("message" | "tool_call" | "state_change"),
    payload (object), timestamp, status
Fragment events omit run_id/task_type (assigned by the runner at stitch time) and
add bookkeeping fields: component, ts_epoch, seq, invocation_id.
"""
from __future__ import annotations

import itertools
import json
import threading
import time
import uuid
from datetime import datetime, timezone
from typing import Any

from datagen.finance.utils.utils import FRAGMENTS_DIR

_MAX_TEXT = 2000  # cap payload text so fragments stay small


def _short_id() -> str:
    return uuid.uuid4().hex[:16]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _truncate(text: str | None) -> str:
    if not text:
        return ""
    return text if len(text) <= _MAX_TEXT else text[:_MAX_TEXT] + "…[truncated]"


def _content_text(content: Any) -> str:
    """Best-effort extraction of text from a genai Content / LlmResponse / dict."""
    if content is None:
        return ""
    parts = getattr(content, "parts", None)
    if parts is None:
        inner = getattr(content, "content", None)  # LlmResponse.content
        parts = getattr(inner, "parts", None)
    if parts is None:
        return _truncate(str(content))
    chunks = [getattr(p, "text", None) for p in parts]
    return _truncate(" ".join(c for c in chunks if c))


class TraceCollector:
    """Per-process collector. Attach its callbacks to every agent in the process."""

    def __init__(self, component: str) -> None:
        self.component = component
        self._seq = itertools.count()
        self._lock = threading.Lock()
        # span stack per thread/invocation; ADK delegation is sequential per process
        self._span_stack: list[str] = []
        FRAGMENTS_DIR.mkdir(parents=True, exist_ok=True)
        self._path = FRAGMENTS_DIR / f"{component}.jsonl"

    # --- low-level emit --------------------------------------------------
    def _emit(
        self,
        *,
        span_id: str,
        parent_span_id: str | None,
        agent_id: str,
        agent_role: str,
        event_type: str,
        payload: dict,
        status: str,
        invocation_id: str | None,
    ) -> None:
        event = {
            "span_id": span_id,
            "parent_span_id": parent_span_id,
            "agent_id": agent_id,
            "agent_role": agent_role,
            "event_type": event_type,
            "payload": payload,
            "status": status,
            "component": self.component,
            "invocation_id": invocation_id,
            "timestamp": _now_iso(),
            "ts_epoch": time.time(),
            "seq": next(self._seq),
        }
        line = json.dumps(event, default=str)
        with self._lock, self._path.open("a") as fh:
            fh.write(line + "\n")

    @property
    def _current_span(self) -> str | None:
        return self._span_stack[-1] if self._span_stack else None

    # --- ADK callbacks ---------------------------------------------------
    def before_agent(self, callback_context: Any) -> None:
        span_id = _short_id()
        agent = getattr(callback_context, "agent_name", self.component)
        self._emit(
            span_id=span_id,
            parent_span_id=self._current_span,
            agent_id=agent,
            agent_role=self.component,
            event_type="state_change",
            payload={"phase": "agent_start"},
            status="in_progress",
            invocation_id=getattr(callback_context, "invocation_id", None),
        )
        self._span_stack.append(span_id)
        return None

    def after_agent(self, callback_context: Any) -> None:
        span_id = self._span_stack.pop() if self._span_stack else _short_id()
        err = getattr(callback_context, "error", None)
        self._emit(
            span_id=span_id,
            parent_span_id=self._current_span,
            agent_id=getattr(callback_context, "agent_name", self.component),
            agent_role=self.component,
            event_type="state_change",
            payload={"phase": "agent_end", "error": _truncate(str(err)) if err else None},
            status="failed" if err else "completed",
            invocation_id=getattr(callback_context, "invocation_id", None),
        )
        return None

    def before_model(self, callback_context: Any, llm_request: Any) -> None:
        contents = getattr(llm_request, "contents", None) or []
        last = _content_text(contents[-1]) if contents else ""
        self._emit(
            span_id=_short_id(),
            parent_span_id=self._current_span,
            agent_id=getattr(callback_context, "agent_name", self.component),
            agent_role=self.component,
            event_type="message",
            payload={"direction": "model_request", "prompt_tail": last},
            status="in_progress",
            invocation_id=getattr(callback_context, "invocation_id", None),
        )
        return None

    def after_model(self, callback_context: Any, llm_response: Any) -> None:
        self._emit(
            span_id=_short_id(),
            parent_span_id=self._current_span,
            agent_id=getattr(callback_context, "agent_name", self.component),
            agent_role=self.component,
            event_type="message",
            payload={"direction": "model_response", "text": _content_text(llm_response)},
            status="completed",
            invocation_id=getattr(callback_context, "invocation_id", None),
        )
        return None

    def before_tool(self, tool: Any, args: Any, tool_context: Any) -> None:
        self._emit(
            span_id=_short_id(),
            parent_span_id=self._current_span,
            agent_id=getattr(tool, "name", "tool"),
            agent_role=self.component,
            event_type="tool_call",
            payload={"phase": "tool_start", "tool": getattr(tool, "name", None), "args": args},
            status="in_progress",
            invocation_id=getattr(tool_context, "invocation_id", None),
        )
        return None

    def after_tool(self, tool: Any, args: Any, tool_context: Any, tool_response: Any) -> None:
        self._emit(
            span_id=_short_id(),
            parent_span_id=self._current_span,
            agent_id=getattr(tool, "name", "tool"),
            agent_role=self.component,
            event_type="tool_call",
            payload={
                "phase": "tool_end",
                "tool": getattr(tool, "name", None),
                "result": _truncate(json.dumps(tool_response, default=str)),
            },
            status="completed",
            invocation_id=getattr(tool_context, "invocation_id", None),
        )
        return None

    def attach(self, agent: Any) -> Any:
        """Wire all six callbacks onto an LlmAgent and return it."""
        self.attach_agent_only(agent)
        agent.before_model_callback = self.before_model
        agent.after_model_callback = self.after_model
        agent.before_tool_callback = self.before_tool
        agent.after_tool_callback = self.after_tool
        return agent

    def attach_agent_only(self, agent: Any) -> Any:
        """Wire just the agent-level callbacks (for agents without a model/tools,
        e.g. RemoteA2aAgent, which only exposes before/after_agent)."""
        agent.before_agent_callback = self.before_agent
        agent.after_agent_callback = self.after_agent
        return agent
