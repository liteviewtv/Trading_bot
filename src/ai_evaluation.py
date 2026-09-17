"""Dependency-free evaluation helpers for AI trading decisions."""

from __future__ import annotations


def evaluate_decision(decision: str, entry_price: float, exit_price: float) -> dict:
    """Evaluate a completed directional decision without executing a trade."""
    action = str(decision).upper()
    if action not in {"BUY", "SELL", "HOLD"}:
        raise ValueError("decision must be BUY, SELL, or HOLD")
    entry = float(entry_price)
    exit_ = float(exit_price)
    if action == "BUY":
        return {"decision": action, "return_pct": (exit_ - entry) / entry * 100 if entry else 0.0,
                "correct": exit_ > entry}
    if action == "SELL":
        return {"decision": action, "return_pct": (entry - exit_) / entry * 100 if entry else 0.0,
                "correct": exit_ < entry}
    return {"decision": action, "return_pct": 0.0, "correct": exit_ == entry}


def summarize_evaluations(records: list[dict]) -> dict:
    if not records:
        return {"count": 0, "accuracy_pct": 0.0, "avg_return_pct": 0.0}
    actionable = [r for r in records if r.get("decision") in {"BUY", "SELL"}]
    correct = sum(bool(r.get("correct")) for r in actionable)
    returns = [float(r.get("return_pct", 0.0)) for r in actionable]
    return {
        "count": len(records),
        "actionable_count": len(actionable),
        "accuracy_pct": correct / len(actionable) * 100 if actionable else 0.0,
        "avg_return_pct": sum(returns) / len(returns) if returns else 0.0,
    }
