from types import SimpleNamespace

from src import mt5_position_manager


def test_rejects_duplicate_symbol(monkeypatch):
    monkeypatch.setattr(mt5_position_manager, "account_info", lambda: SimpleNamespace(equity=10000))
    monkeypatch.setattr(mt5_position_manager, "positions", lambda: [SimpleNamespace(symbol="EURUSD")])
    state = mt5_position_manager.inspect_positions("EURUSD", max_open_positions=5)
    assert state.can_open is False
    assert "already exists" in state.reason


def test_rejects_when_position_limit_reached(monkeypatch):
    monkeypatch.setattr(mt5_position_manager, "account_info", lambda: SimpleNamespace(equity=10000))
    monkeypatch.setattr(mt5_position_manager, "positions", lambda: [SimpleNamespace(symbol="EURUSD"), SimpleNamespace(symbol="GBPUSD")])
    state = mt5_position_manager.inspect_positions("XAUUSD", max_open_positions=2)
    assert state.can_open is False
    assert "Maximum open positions" in state.reason


def test_allows_new_symbol_below_limit(monkeypatch):
    monkeypatch.setattr(mt5_position_manager, "account_info", lambda: SimpleNamespace(equity=10000))
    monkeypatch.setattr(mt5_position_manager, "positions", lambda: [SimpleNamespace(symbol="EURUSD")])
    state = mt5_position_manager.inspect_positions("XAUUSD", max_open_positions=2)
    assert state.can_open is True
    assert state.open_count == 1
