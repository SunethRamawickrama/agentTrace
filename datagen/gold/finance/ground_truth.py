"""Expected answers, computed in Python from the datasets (never by an LLM).

Keeping ground truth here — derived from the same CSVs the agents read — is what
makes the gold set deterministically verifiable.
"""
from __future__ import annotations

from datagen.finance.utils import utils as datasets

# Fixed inputs used by prompts that are not themselves stored in a dataset.
DEPRECIATION = {"cost": 100000.0, "salvage": 10000.0, "life_years": 5}
TAXABLE_INCOME = 50000.0
DEDUCTIBLE_CATEGORIES = ["office", "software", "travel"]
RECONCILE_ACCOUNT = "cash"


def total_revenue_2024() -> float:
    return datasets.balance_sheet_value("total_revenue", "2024")


def net_income_2024() -> float:
    return datasets.balance_sheet_value("net_income", "2024")


def net_profit_margin() -> float:
    return net_income_2024() / total_revenue_2024()


def current_ratio() -> float:
    return (datasets.balance_sheet_value("current_assets", "2024")
            / datasets.balance_sheet_value("current_liabilities", "2024"))


def ar_turnover() -> float:
    return total_revenue_2024() / datasets.balance_sheet_value("accounts_receivable", "2024")


def yoy_revenue_growth_pct() -> float:
    prev = datasets.balance_sheet_value("total_revenue", "2023")
    return (total_revenue_2024() - prev) / prev * 100.0


def reconciliation_difference() -> float:
    debit, credit = datasets.ledger_totals(RECONCILE_ACCOUNT)
    return debit - credit


def income_tax_owed() -> float:
    return datasets.tax_owed(TAXABLE_INCOME)


def effective_tax_rate() -> float:
    return datasets.tax_owed(TAXABLE_INCOME) / TAXABLE_INCOME


def straight_line_depreciation() -> float:
    d = DEPRECIATION
    return (d["cost"] - d["salvage"]) / d["life_years"]


def deductible_expenses() -> dict[str, float]:
    by_cat = datasets.expenses_by_category()
    return {c: by_cat[c] for c in DEDUCTIBLE_CATEGORIES}


def top3_expense_categories() -> list[str]:
    by_cat = datasets.expenses_by_category()
    return [c for c, _ in sorted(by_cat.items(), key=lambda kv: kv[1], reverse=True)][:3]
