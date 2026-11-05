"""Pure metric functions for the evaluation harness (no I/O, no model calls)."""
from __future__ import annotations

import statistics
from collections import Counter, defaultdict


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    s = sorted(values)
    k = max(0, min(len(s) - 1, round(p / 100 * (len(s) - 1))))
    return s[k]


def latency_stats(values: list[float]) -> dict:
    if not values:
        return {"n": 0, "mean": None, "median": None, "p95": None}
    return {"n": len(values), "mean": statistics.fmean(values), "median": statistics.median(values), "p95": percentile(values, 95)}


def classification(rows: list[dict]) -> dict:
    """rows: dicts with true, pred. Rows with pred None (failed run) count as wrong."""
    total = len(rows)
    correct = sum(1 for r in rows if r["pred"] == r["true"])
    per_class: dict[str, dict[str, int]] = defaultdict(lambda: {"correct": 0, "total": 0})
    confusion: dict[str, Counter] = defaultdict(Counter)
    for r in rows:
        per_class[r["true"]]["total"] += 1
        per_class[r["true"]]["correct"] += r["pred"] == r["true"]
        confusion[r["true"]][r["pred"] or "FAILED"] += 1
    return {
        "correct": correct,
        "total": total,
        "accuracy": (correct / total) if total else None,
        "per_class": dict(per_class),
        "confusion": {k: dict(v) for k, v in confusion.items()},
    }


def decline_or_ask(rows: list[dict]) -> dict:
    """How often non-civic images are declined and ambiguous ones get a question instead of a forced label."""
    no_issue = [r for r in rows if r["true"] == "no_civic_issue"]
    ambiguous = [r for r in rows if r["true"] == "unclear"]
    declined = sum(1 for r in no_issue if r["pred"] == "no_civic_issue")
    asked = sum(1 for r in ambiguous if r.get("asked") or r["pred"] == "unclear")
    forced = sum(1 for r in no_issue + ambiguous if r["pred"] not in (None, "no_civic_issue", "unclear") and not r.get("asked"))
    return {
        "no_issue_declined": declined, "no_issue_total": len(no_issue),
        "ambiguous_asked": asked, "ambiguous_total": len(ambiguous),
        "forced_label": forced, "forced_label_denominator": len(no_issue) + len(ambiguous),
    }


def complaint_stats(complaints: list[dict]) -> dict:
    """complaints: dicts with passed, n_issues, complete, regenerated."""
    n = len(complaints)
    if not n:
        return {"n": 0}
    return {
        "n": n,
        "complete": sum(c["complete"] for c in complaints),
        "validator_passed_final": sum(c["passed"] for c in complaints),
        "passed_first_try": sum(1 for c in complaints if c["passed"] and not c["regenerated"]),
        "total_issues_flagged": sum(c["n_issues"] for c in complaints),
    }
