"""AI-assisted signal filter.

The model is deliberately an advisory layer: it can approve, reject, or hold a
strategy signal, but it cannot place orders or bypass risk controls.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AIFilterDecision:
    action: str
    confidence: float
    reason: str


def filter_signal(strategy_signal, ai_decision: AIFilterDecision, min_confidence: float = 0.60) -> AIFilterDecision:
    """Accept only a matching, sufficiently confident AI decision."""
    if not 0.0 <= min_confidence <= 1.0:
        raise ValueError("min_confidence must be between 0 and 1")
    strategy_action = getattr(strategy_signal, "action", None)
    action = ai_decision.action.upper()
    if action not in {"BUY", "SELL", "HOLD"}:
        raise ValueError("AI action must be BUY, SELL, or HOLD")
    if action == "HOLD" or ai_decision.confidence < min_confidence or action != strategy_action:
        return AIFilterDecision("HOLD", ai_decision.confidence, "AI filter rejected strategy signal: " + ai_decision.reason)
    return ai_decision
