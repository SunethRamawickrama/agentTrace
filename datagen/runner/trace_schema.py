"""JSON Schema for the canonical trace event, plus a validate helper."""
from __future__ import annotations

from jsonschema import Draft202012Validator

EVENT_SCHEMA = {
    "type": "object",
    "required": [
        "run_id", "span_id", "parent_span_id", "agent_id", "agent_role",
        "task_type", "event_type", "payload", "timestamp", "status",
    ],
    "properties": {
        "run_id": {"type": "string"},
        "span_id": {"type": "string"},
        "parent_span_id": {"type": ["string", "null"]},
        "agent_id": {"type": "string"},
        "agent_role": {"type": "string"},
        "task_type": {"type": "string"},
        "event_type": {"enum": ["message", "tool_call", "state_change"]},
        "payload": {"type": "object"},
        "timestamp": {"type": "string"},
        "status": {"enum": ["in_progress", "completed", "failed", "timed_out"]},
    },
    "additionalProperties": True,
}

_validator = Draft202012Validator(EVENT_SCHEMA)


def validate_event(event: dict) -> list[str]:
    """Return a list of human-readable schema errors (empty if valid)."""
    return [e.message for e in _validator.iter_errors(event)]
