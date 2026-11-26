"""Serve one finance specialist as an A2A server.

Usage:
    python -m datagen.finance.agents.serve <specialist_name>

Each specialist runs in its own process on its own port, with a TraceCollector
writing canonical trace-event fragments. The orchestrator reaches them over A2A.

the method "to_a2a" converts the specialist sub agents into a2a compatible agents
"""
from __future__ import annotations

import sys

import uvicorn
from google.adk.a2a.utils.agent_to_a2a import to_a2a

from datagen.finance.agents.sub_agents import (
    accounting_agent,
    analytics_agent,
    data_agent,
    tax_agent,
)
from datagen.finance.utils.tracing import TraceCollector

SPECIALISTS_SUBAGENT = {
    data_agent.NAME: data_agent,
    accounting_agent.NAME: accounting_agent,
    tax_agent.NAME: tax_agent,
    analytics_agent.NAME: analytics_agent,
}


def serve_specialist_subagent(specialist_name: str):
    specialist = SPECIALISTS_SUBAGENT[specialist_name]
    agent = specialist.build_agent()
    TraceCollector(component=specialist_name).attach(agent)
    return to_a2a(agent, host="localhost", port=specialist.PORT), specialist.PORT


def main(argv: list[str]) -> None:
    if len(argv) != 2 or argv[1] not in SPECIALISTS_SUBAGENT:
        sys.exit(f"usage: python -m datagen.finance.agents.serve <{'|'.join(SPECIALISTS_SUBAGENT)}>")
    specialist_name = argv[1]
    app, port = serve_specialist_subagent(specialist_name)
    uvicorn.run(app, host="localhost", port=port, log_level="warning")


if __name__ == "__main__":
    main(sys.argv)
