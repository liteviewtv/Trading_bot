from types import SimpleNamespace

from src import mt5_auto_cycle
from src.ai_filter import AIFilterDecision


def test_ai_rejects_mismatched_signal(monkeypatch):
    monkeypatch.setattr(mt5_auto_cycle, "scan_assets", lambda assets: [
        SimpleNamespace(requested="EURUSD", symbol="EURUSD", signal=SimpleNamespace(action="BUY"), error=None)
    ])
    monkeypatch.setattr(mt5_auto_cycle, "inspect_positions", lambda *args, **kwargs: SimpleNamespace(can_open=True, reason="ok"))
    monkeypatch.setattr(mt5_auto_cycle, "run_demo_cycle", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("must not execute")))
    result = mt5_auto_cycle.run_auto_demo_cycle(
        execute=True,
        ai_decisions={"EURUSD": AIFilterDecision("SELL", 0.95, "opposes setup")},
    )
    assert result.executed == []
    assert "rejected" in result.skipped[0]


def test_ai_allows_matching_confident_signal(monkeypatch):
    monkeypatch.setattr(mt5_auto_cycle, "scan_assets", lambda assets: [
        SimpleNamespace(requested="EURUSD", symbol="EURUSD", signal=SimpleNamespace(action="BUY"), error=None)
    ])
    monkeypatch.setattr(mt5_auto_cycle, "inspect_positions", lambda *args, **kwargs: SimpleNamespace(can_open=True, reason="ok"))
    monkeypatch.setattr(mt5_auto_cycle, "run_demo_cycle", lambda symbol, execute=True: SimpleNamespace(symbol=symbol, submitted=True))
    result = mt5_auto_cycle.run_auto_demo_cycle(
        execute=True,
        ai_decisions={"EURUSD": AIFilterDecision("BUY", 0.90, "setup confirmed")},
    )
    assert len(result.executed) == 1
