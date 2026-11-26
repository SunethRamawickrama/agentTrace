"""The brief finance gold set: exact prompt + deterministic expected answer.

Expected values come from ground_truth.py (computed from the datasets), so the
whole set stays deterministically verifiable.
"""
from __future__ import annotations

from dataclasses import dataclass

from datagen.gold.finance import ground_truth as gt


@dataclass(frozen=True)
class GoldCase:
    case_id: str
    task_type: str
    prompt: str
    verifier: dict  # {kind, expected, tol?}


def build_cases() -> list[GoldCase]:
    d = gt.DEPRECIATION
    return [
        GoldCase("fin-01", "total_revenue",
                 "What was total revenue in 2024? Answer with the number only.",
                 {"kind": "number", "expected": gt.total_revenue_2024(), "tol": 1.0}),
        GoldCase("fin-02", "net_income",
                 "What was net income in 2024? Answer with the number only.",
                 {"kind": "number", "expected": gt.net_income_2024(), "tol": 1.0}),
        GoldCase("fin-03", "net_profit_margin",
                 "Compute the 2024 net profit margin (net income / total revenue) "
                 "as a decimal. Answer with the number only.",
                 {"kind": "number", "expected": gt.net_profit_margin(), "tol": 0.005}),
        GoldCase("fin-04", "current_ratio",
                 "Compute the 2024 current ratio (current assets / current "
                 "liabilities). Answer with the number only.",
                 {"kind": "number", "expected": gt.current_ratio(), "tol": 0.01}),
        GoldCase("fin-05", "ar_turnover",
                 "Compute the 2024 accounts-receivable turnover (total revenue / "
                 "accounts receivable). Answer with the number only.",
                 {"kind": "number", "expected": gt.ar_turnover(), "tol": 0.01}),
        GoldCase("fin-06", "yoy_revenue_growth",
                 "Compute year-over-year revenue growth from 2023 to 2024 as a "
                 "percentage. Answer with the number only.",
                 {"kind": "number", "expected": gt.yoy_revenue_growth_pct(), "tol": 0.1}),
        GoldCase("fin-07", "reconciliation_difference",
                 "For the 'cash' ledger account, compute total debits minus total "
                 "credits. Answer with the number only.",
                 {"kind": "number", "expected": gt.reconciliation_difference(), "tol": 1.0}),
        GoldCase("fin-08", "income_tax_owed",
                 "Compute the progressive income tax owed on taxable income of "
                 f"{int(gt.TAXABLE_INCOME)}. Answer with the number only.",
                 {"kind": "number", "expected": gt.income_tax_owed(), "tol": 1.0}),
        GoldCase("fin-09", "effective_tax_rate",
                 "Compute the effective tax rate on taxable income of "
                 f"{int(gt.TAXABLE_INCOME)} as a decimal. Answer with the number only.",
                 {"kind": "number", "expected": gt.effective_tax_rate(), "tol": 0.005}),
        GoldCase("fin-10", "straight_line_depreciation",
                 "Compute the annual straight-line depreciation for an asset costing "
                 f"{int(d['cost'])} with salvage value {int(d['salvage'])} over "
                 f"{d['life_years']} years. Answer with the number only.",
                 {"kind": "number", "expected": gt.straight_line_depreciation(), "tol": 1.0}),
        GoldCase("fin-11", "deductible_expenses",
                 "Sum expenses for these categories: office, software, travel. "
                 "Return a compact JSON object mapping each category to its total, "
                 "e.g. {\"office\": 0}.",
                 {"kind": "json_object", "expected": gt.deductible_expenses(), "tol": 1.0}),
        GoldCase("fin-12", "top3_expense_categories",
                 "Return the 3 highest-spend expense categories as a compact JSON "
                 "array of category names, highest first, e.g. [\"a\",\"b\",\"c\"].",
                 {"kind": "json_list", "expected": gt.top3_expense_categories()}),
    ]
