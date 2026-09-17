from types import SimpleNamespace

from src import mt5_auto_cycle
from src.trade_journal import read_entries


def test_auto_cycle_journals_skipped_signal(tmp_path, monkeypatch):
    monkeypatch.setattr(mt5_auto_cycle, "scan_assets", lambda assets: [
        SimpleNamespace(requested="EURUSD", symbol="EURUSD", signal=None, error="Symbol unavailable")
    ])
    result = mt5_auto_cycle.run_auto_demo_cycle(journal_path=tmp_path / "trades.jsonl")
    entries = read_entries(tmp_path / "trades.jsonl")
    assert result.executed == []
    assert entries[0].event == "skipped"
    assert entries[0].reason == "Symbol unavailable"


def test_auto_cycle_journals_signal_when_execution_disabled(tmp_path, monkeypatch):
    monkeypatch.setattr(mt5_auto_cycle, "scan_assets", lambda assets: [
        SimpleNamespace(requested="EURUSD", symbol="EURUSD", signal=SimpleNamespace(action="BUY"), error=None)
    ])
    mt5_auto_cycle.run_auto_demo_cycle(journal_path=tmp_path / "trades.jsonl")
    entries = read_entries(tmp_path / "trades.jsonl")
    assert entries[0].event == "signal"
    assert entries[0].action == "BUY"
    assert entries[0].reason == "execution disabled"
