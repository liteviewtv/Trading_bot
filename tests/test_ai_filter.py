from types import SimpleNamespace

import pytest

from src.ai_filter import AIFilterDecision, filter_signal


def test_matching_confident_ai_signal_is_accepted():
    result = filter_signal(SimpleNamespace(action="BUY"), AIFilterDecision("BUY", 0.85, "trend aligned"))
    assert result.action == "BUY"


def test_low_confidence_signal_becomes_hold():
    result = filter_signal(SimpleNamespace(action="BUY"), AIFilterDecision("BUY", 0.40, "weak setup"))
    assert result.action == "HOLD"


def test_conflicting_signal_becomes_hold():
    result = filter_signal(SimpleNamespace(action="BUY"), AIFilterDecision("SELL", 0.90, "bearish regime"))
    assert result.action == "HOLD"


def test_invalid_action_rejected():
    with pytest.raises(ValueError):
        filter_signal(SimpleNamespace(action="BUY"), AIFilterDecision("LONG", 0.9, "bad"))
