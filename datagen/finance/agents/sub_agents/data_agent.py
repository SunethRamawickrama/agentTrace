"""Data-retrieval sub-agent: looks up raw figures from the datasets."""
from __future__ import annotations

from google.adk.agents import LlmAgent

from datagen.finance.agents.tools import (
    get_balance_sheet_value,
    get_expenses_by_category,
    get_ledger_totals,
)
from datagen.finance.utils.utils import get_model

NAME = "data_agent"
PORT = 8101

INSTRUCTION = """You are a financial data-retrieval agent.
Use your tools to look up the exact figure(s) the caller asks for.
Return ONLY the requested value as a bare number (no currency symbols, no words,
no explanation). If a value cannot be found, return the single word: UNKNOWN."""


def build_agent() -> LlmAgent:
    return LlmAgent(
        name=NAME,
        model=get_model(),
        description="Retrieves raw financial figures (balance sheet, ledger, expenses).",
        instruction=INSTRUCTION,
        tools=[get_balance_sheet_value, get_ledger_totals, get_expenses_by_category],
    )
