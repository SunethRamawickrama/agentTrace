"""Tax sub-agent: progressive tax owed and effective rate (reasons over the table)."""
from __future__ import annotations

from google.adk.agents import LlmAgent

from datagen.finance.agents.tools import get_tax_table
from datagen.finance.utils.utils import get_model

NAME = "tax_agent"
PORT = 8103

INSTRUCTION = """You are a tax agent. Use get_tax_table to fetch the progressive
brackets, then compute the answer yourself.

- Tax owed: apply each bracket's rate only to the portion of taxable income that
  falls within that bracket, and sum. The top bracket (upper = null) applies to
  everything above its lower bound.
- Effective tax rate = total_tax_owed / taxable_income (a decimal, e.g. 0.2).

Return ONLY the final numeric result as a bare number — no words, no percent
sign, no explanation."""


def build_agent() -> LlmAgent:
    return LlmAgent(
        name=NAME,
        model=get_model(),
        description="Computes progressive income tax owed and effective tax rate.",
        instruction=INSTRUCTION,
        tools=[get_tax_table],
    )
