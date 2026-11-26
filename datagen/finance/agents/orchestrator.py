"""Root orchestrator: decomposes a finance task and delegates to specialists over A2A.

sub-agents are running on different uvicorn servers and their own process spaces, the orchestrator 
runs on the program's python process. The orchestrator - subagent communication happens through 
HTTP POST, the orchestrator will send the instructions through the payload. Each sub agent will be started 
in their own servers and their agent cards will expose the necessary metadata through the agent cards. 
In this codebase, the google adk is used for agent dev and the a2a functionalities from that module is used
instead of the a2a-sdk. This eliminates the need to manually construct the agent cards and wire the agents, 
and make the process easier and reducing the boilerplate code. 

Google codelab a2a sdk example: https://codelabs.developers.google.com/intro-a2a-purchasing-concierge#7
"""

from __future__ import annotations

from google.adk.agents import LlmAgent
from google.adk.agents.remote_a2a_agent import (
    AGENT_CARD_WELL_KNOWN_PATH,
    RemoteA2aAgent,
)

from datagen.finance.agents.sub_agents import (
    accounting_agent,
    analytics_agent,
    data_agent,
    tax_agent,
)
from datagen.finance.utils.utils import get_model

NAME = "orchestrator"

INSTRUCTION = """You are the coordinator of a finance team. Route each task to the
one specialist best suited to it, then return that specialist's answer as your
final response, unchanged and with no extra commentary.

Routing guide:
- data_agent: look up a single raw figure (e.g. "total revenue in 2024").
- accounting_agent: current ratio, accounts-receivable turnover, ledger
  reconciliation difference, straight-line depreciation.
- tax_agent: income tax owed, effective tax rate.
- analytics_agent: net profit margin, year-over-year growth, top-N expense
  categories, deductible-expense breakdowns.

Your final answer must contain ONLY what the task asks for (a bare number, or
compact JSON) — never prose, labels, units, or currency symbols."""


def _sub_agent_to_remote_a2a(llm_agent) -> RemoteA2aAgent:
    return RemoteA2aAgent(
        name=llm_agent.NAME,
        description=llm_agent.build_agent().description,
        agent_card=f"http://localhost:{llm_agent.PORT}{AGENT_CARD_WELL_KNOWN_PATH}",
    )


def build_orchestrator() -> LlmAgent:
    return LlmAgent(
        name=NAME,
        model=get_model(),
        description="Coordinates the finance specialist agents.",
        instruction=INSTRUCTION,
        sub_agents=[
            _sub_agent_to_remote_a2a(data_agent),
            _sub_agent_to_remote_a2a(accounting_agent),
            _sub_agent_to_remote_a2a(tax_agent),
            _sub_agent_to_remote_a2a(analytics_agent),
        ],
    )
