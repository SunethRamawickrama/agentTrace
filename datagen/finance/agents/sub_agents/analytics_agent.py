"""Analytics sub-agent: growth, margins, top-N and category breakdowns."""
from __future__ import annotations

from google.adk.agents import LlmAgent

from datagen.finance.agents.tools import get_balance_sheet_value, get_expenses_by_category
from datagen.finance.utils.utils import get_model

NAME = "analytics_agent"
PORT = 8104

INSTRUCTION = """You are a financial analytics agent. Use your tools to fetch raw
figures, then compute the requested analysis yourself.

- net profit margin = net_income / total_revenue (a decimal, e.g. 0.18)
- year-over-year revenue growth percent =
    (revenue_this_year - revenue_last_year) / revenue_last_year * 100
- top-N expense categories: the N categories with the largest totals, highest first
- deductible expenses: sum amounts only for the categories the caller names

Return ONLY the result with no prose:
- a bare number for numeric questions,
- a compact JSON array for ranked lists, e.g. ["office","software"],
- a compact JSON object for category breakdowns, e.g. {"office":10000}."""


def build_agent() -> LlmAgent:
    return LlmAgent(
        name=NAME,
        model=get_model(),
        description="Computes growth, margins, rankings and category breakdowns.",
        instruction=INSTRUCTION,
        tools=[get_balance_sheet_value, get_expenses_by_category],
    )
