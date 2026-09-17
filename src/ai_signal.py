"""AI-ready signal analysis interface.

The default implementation is deterministic and free: it acts as a safety
filter around the existing strategy. A future local model can implement the
same interface without changing execution or risk controls.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AIAnalysis:
    decision: str
    confidence: float
    reason: str
    model: str = "deterministic"


class SignalAnalyzer:
    def analyze(self, signal) -> AIAnalysis:
        action = str(getattr(signal, "action", "HOLD")).upper()
        if action not in {"BUY", "SELL"}:
            return AIAnalysis("HOLD", 1.0, "No actionable strategy signal")
        return AIAnalysis(
            action,
            0.50,
            "AI layer currently confirms the existing strategy signal; no external model is required.",
        )


def analyze_signal(signal, analyzer: SignalAnalyzer | None = None) -> AIAnalysis:
    return (analyzer or SignalAnalyzer()).analyze(signal)
