"""Shared utilities for the finance datagen system."""
from __future__ import annotations

import csv
import os
from pathlib import Path
from typing import Any

# --- Path configuration -------------------------------------------------------

# repo root = .../agentTrace (this file is datagen/finance/utils/utils.py)
ROOT = Path(__file__).resolve().parents[3]

DATASETS_DIR = ROOT / "data" / "finance" / "datasets"
TRACES_DIR = ROOT / "data" / "traces" / "finance"
FRAGMENTS_DIR = TRACES_DIR / "_fragments"

# --- Model configuration -------------------------------------------------------

DEFAULT_GEMINI_MODEL = "gemini-3.8-flash"
DEFAULT_GROQ_MODEL = "groq/qwen/qwen3.8-27b"
DEFAULT_PROVIDER = "groq"


def get_model() -> Any:
    """Return a value suitable for ``LlmAgent(model=...)``."""
    provider = os.getenv("AGENTTRACE_PROVIDER", DEFAULT_PROVIDER).lower()
    if provider == "groq":
        from google.adk.models.lite_llm import LiteLlm  # requires google-adk[extensions]

        return LiteLlm(model=os.getenv("AGENTTRACE_MODEL", DEFAULT_GROQ_MODEL))
    return os.getenv("AGENTTRACE_MODEL", DEFAULT_GEMINI_MODEL)

# --- Dataset operations -------------------------------------------------------


def load_dataset(name: str) -> list[dict]:
    """Load a dataset CSV (without the .csv extension) as a list of row dicts."""
    path = DATASETS_DIR / f"{name}.csv"
    if not path.exists():
        raise FileNotFoundError(
            f"unknown dataset {name!r}; available: "
            + ", ".join(sorted(p.stem for p in DATASETS_DIR.glob("*.csv")))
        )
    with path.open(newline="") as fh:
        return list(csv.DictReader(fh))


def balance_sheet_value(line_item: str, period: str) -> float:
    for row in load_dataset("balance_sheet"):
        if row["line_item"] == line_item and row["period"] == str(period):
            return float(row["amount"])
    raise KeyError(f"no balance_sheet row for {line_item!r} period {period!r}")


def expenses_by_category() -> dict[str, float]:
    totals: dict[str, float] = {}
    for row in load_dataset("transactions"):
        totals[row["category"]] = totals.get(row["category"], 0.0) + float(row["amount"])
    return totals


def ledger_totals(account: str) -> tuple[float, float]:
    """Return (total_debit, total_credit) for an account."""
    debit = credit = 0.0
    for row in load_dataset("ledger"):
        if row["account"] == account:
            debit += float(row["debit"])
            credit += float(row["credit"])
    return debit, credit


def tax_brackets() -> list[tuple[float, float | None, float]]:
    out: list[tuple[float, float | None, float]] = []
    for row in load_dataset("tax_table"):
        upper = float(row["upper"]) if row["upper"] else None
        out.append((float(row["lower"]), upper, float(row["rate"])))
    return out


def tax_owed(taxable_income: float) -> float:
    owed = 0.0
    for lower, upper, rate in tax_brackets():
        if taxable_income <= lower:
            break
        top = taxable_income if upper is None else min(taxable_income, upper)
        owed += (top - lower) * rate
    return owed
