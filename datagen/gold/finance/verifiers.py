"""Deterministic, graded verifiers.

Each returns a dict: {score (0..1), passed (bool), category, detail}.
``category`` is one of: pass, fail_accuracy, fail_format, fail_other — the three
DATA.md failure buckets plus a catch-all (empty / hallucinated / no answer).
"""
from __future__ import annotations

import json
import re

PASS = "pass"
FAIL_ACCURACY = "fail_accuracy"
FAIL_FORMAT = "fail_format"
FAIL_OTHER = "fail_other"

_NUM_RE = re.compile(r"[-+]?\d[\d,]*\.?\d*")


def _clamp(x: float) -> float:
    return max(0.0, min(1.0, x))


def _result(score: float, passed: bool, category: str, detail: str) -> dict:
    return {"score": round(score, 4), "passed": passed, "category": category, "detail": detail}


def _parse_number(text: str) -> float | None:
    m = _NUM_RE.search(text.replace("%", ""))
    if not m:
        return None
    try:
        return float(m.group(0).replace(",", ""))
    except ValueError:
        return None


def _is_clean_number(text: str) -> bool:
    try:
        float(text.strip().replace(",", "").rstrip("%"))
        return True
    except ValueError:
        return False


def verify_number(output: str, expected: float, tol: float) -> dict:
    output = (output or "").strip()
    value = _parse_number(output)
    if value is None:
        return _result(0.0, False, FAIL_OTHER, f"no number found in {output!r}")
    denom = max(abs(expected), 1.0)
    closeness = _clamp(1 - abs(value - expected) / denom)
    passed = abs(value - expected) <= tol
    if passed and _is_clean_number(output):
        return _result(1.0, True, PASS, f"{value} within ±{tol} of {expected}")
    if passed:
        return _result(0.6, False, FAIL_FORMAT,
                       f"correct value {value} but wrapped in text/units")
    return _result(closeness, False, FAIL_ACCURACY,
                   f"got {value}, expected {expected} (±{tol})")


def _extract_json(output: str):
    """Return (parsed, clean) where clean means the whole output was just the JSON."""
    output = (output or "").strip()
    try:
        return json.loads(output), True
    except json.JSONDecodeError:
        pass
    for opener, closer in (("{", "}"), ("[", "]")):
        i, j = output.find(opener), output.rfind(closer)
        if 0 <= i < j:
            try:
                return json.loads(output[i:j + 1]), False
            except json.JSONDecodeError:
                continue
    return None, False


def verify_json_object(output: str, expected: dict, tol: float) -> dict:
    parsed, clean = _extract_json(output)
    if not isinstance(parsed, dict):
        return _result(0.0, False, FAIL_OTHER, f"no JSON object found in {output!r}")
    hits = 0
    for key, exp in expected.items():
        try:
            if abs(float(parsed.get(key)) - float(exp)) <= tol:
                hits += 1
        except (TypeError, ValueError):
            pass
    score = hits / len(expected)
    all_correct = hits == len(expected)
    if all_correct and clean:
        return _result(1.0, True, PASS, "all fields present and correct")
    if all_correct:
        return _result(0.6, False, FAIL_FORMAT, "correct fields but wrapped in text")
    return _result(score, False, FAIL_ACCURACY,
                   f"{hits}/{len(expected)} fields correct; got {parsed}")


def verify_json_list(output: str, expected: list) -> dict:
    parsed, clean = _extract_json(output)
    if not isinstance(parsed, list):
        return _result(0.0, False, FAIL_OTHER, f"no JSON array found in {output!r}")
    norm = [str(x).strip().lower() for x in parsed]
    exp = [str(x).strip().lower() for x in expected]
    if norm == exp and clean:
        return _result(1.0, True, PASS, "exact ordered match")
    if norm == exp:
        return _result(0.6, False, FAIL_FORMAT, "correct list but wrapped in text")
    overlap = len(set(norm) & set(exp)) / len(exp)
    return _result(overlap, False, FAIL_ACCURACY, f"got {parsed}, expected {expected}")


def verify(spec: dict, output: str) -> dict:
    kind = spec["kind"]
    if kind == "number":
        return verify_number(output, spec["expected"], spec.get("tol", 0.01))
    if kind == "json_object":
        return verify_json_object(output, spec["expected"], spec.get("tol", 0.01))
    if kind == "json_list":
        return verify_json_list(output, spec["expected"])
    raise ValueError(f"unknown verifier kind {kind!r}")
