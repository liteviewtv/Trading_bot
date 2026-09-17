"""AI-ready signal analysis with an optional local-model adapter.

The model remains advisory-only: it cannot place orders or bypass risk controls.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class AIAnalysis:
    decision: str
    confidence: float
    reason: str
    model: str = "deterministic"


class ModelAdapter(Protocol):
    def analyze(self, signal, context: dict | None = None) -> AIAnalysis: ...


class DeterministicAnalyzer:
    def analyze(self, signal, context: dict | None = None) -> AIAnalysis:
        action = str(getattr(signal, "action", "HOLD")).upper()
        if action not in {"BUY", "SELL"}:
            return AIAnalysis("HOLD", 1.0, "No actionable strategy signal")
        return AIAnalysis(action, 0.50, "No local model configured; held for safety")


class LocalModelAnalyzer:
    """Adapter for a local model callable; no paid API dependency."""

    def __init__(self, model_callable):
        self.model_callable = model_callable

    def analyze(self, signal, context: dict | None = None) -> AIAnalysis:
        result = self.model_callable(signal, context or {})
        if not isinstance(result, AIAnalysis):
            raise TypeError("Local model must return AIAnalysis")
        return result


def analyze_signal(signal, analyzer: ModelAdapter | None = None, context: dict | None = None) -> AIAnalysis:
    return (analyzer or DeterministicAnalyzer()).analyze(signal, context)
