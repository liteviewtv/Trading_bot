from types import SimpleNamespace

from src.ai_signal import SignalAnalyzer, analyze_signal


def test_ai_confirms_buy_signal():
    result = analyze_signal(SimpleNamespace(action="BUY"))
    assert result.decision == "BUY"
    assert 0 <= result.confidence <= 1
    assert result.model == "deterministic"


def test_ai_holds_without_action():
    result = SignalAnalyzer().analyze(SimpleNamespace(action="HOLD"))
    assert result.decision == "HOLD"
    assert result.confidence == 1.0
