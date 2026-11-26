"""Accounting sub-agent: ratios, reconciliation, depreciation (reasons over raw data)."""
from __future__ import annotations

from google.adk.agents import LlmAgent

from datagen.finance.agents.tools import get_balance_sheet_value, get_ledger_totals
from datagen.finance.utils.utils import get_model

NAME = "accounting_agent"
PORT = 8102

INSTRUCTION = """You are an accounting agent. Use your tools to fetch the raw
figures you need, then compute the requested result yourself.

Formulas:
- current ratio = current_assets / current_liabilities
- accounts receivable turnover = total_revenue / accounts_receivable
- reconciliation difference for an account = total_debit - total_credit
- straight-line depreciation per year = (cost - salvage) / useful_life_years

Return ONLY the final numeric result as a bare number — no words, no units,
no explanation."""


def build_agent() -> LlmAgent:
    return LlmAgent(
        name=NAME,
        model=get_model(),
        description="Computes accounting ratios, reconciliations and depreciation.",
        instruction=INSTRUCTION,
        tools=[get_balance_sheet_value, get_ledger_totals],
    )
