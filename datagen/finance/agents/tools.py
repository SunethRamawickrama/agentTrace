"""Agent tools over the mock datasets.

These expose raw figures only — they never compute a final answer. The agents
must reason/do the arithmetic themselves, which is exactly where a free-tier model
makes natural mistakes (the failures this phase harvests).
"""
from __future__ import annotations

from datagen.finance.utils import utils


def get_balance_sheet_value(line_item: str, period: str) -> dict:
    """Return the balance-sheet amount for a line item and period.

    Args:
        line_item: e.g. "total_revenue", "net_income", "current_assets",
            "current_liabilities", "accounts_receivable".
        period: fiscal year as a string, e.g. "2024".
    """
    try:
        return {"line_item": line_item, "period": period,
                "amount": utils.balance_sheet_value(line_item, str(period))}
    except KeyError as exc:
        return {"error": str(exc)}


def get_expenses_by_category() -> dict:
    """Return total expense amount per category from the transactions ledger."""
    return {"expenses_by_category": utils.expenses_by_category()}


def get_ledger_totals(account: str) -> dict:
    """Return total debits and credits recorded for a ledger account."""
    debit, credit = utils.ledger_totals(account)
    return {"account": account, "total_debit": debit, "total_credit": credit}


def get_tax_table() -> dict:
    """Return the progressive tax brackets as a list of {lower, upper, rate}.

    ``upper`` is null for the top (open-ended) bracket.
    """
    brackets = [{"lower": lo, "upper": up, "rate": rate}
                for lo, up, rate in utils.tax_brackets()]
    return {"brackets": brackets}
