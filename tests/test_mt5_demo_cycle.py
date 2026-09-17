from types import SimpleNamespace

import pandas as pd

from src import mt5_demo_cycle


def test_cycle_does_not_execute_by_default(monkeypatch):
    monkeypatch.setattr(mt5_demo_cycle, "MT5Settings", SimpleNamespace(from_env=lambda: object()))
    monkeypatch.setattr(mt5_demo_cycle, "connect", lambda settings: None)
    monkeypatch.setattr(mt5_demo_cycle, "disconnect", lambda: None)
    monkeypatch.setattr(mt5_demo_cycle, "account_info", lambda: SimpleNamespace(equity=10_000))
    monkeypatch.setattr(mt5_demo_cycle, "bars", lambda symbol: pd.DataFrame({"close": [10.0] * 60}))
    monkeypatch.setattr(mt5_demo_cycle, "generate_mt5_signal", lambda symbol, frame: SimpleNamespace(action="BUY"))
    called = {"order": False}

    def fail_if_called(*args, **kwargs):
        called["order"] = True
        raise AssertionError("demo order must not be submitted when execute=False")

    monkeypatch.setattr(mt5_demo_cycle, "submit_demo_market_order", fail_if_called)
    result = mt5_demo_cycle.run_demo_cycle("EURUSD")

    assert result.submitted is False
    assert called["order"] is False
    assert "execution disabled" in result.message


def test_cycle_submits_when_explicitly_enabled(monkeypatch):
    monkeypatch.setattr(mt5_demo_cycle, "MT5Settings", SimpleNamespace(from_env=lambda: object()))
    monkeypatch.setattr(mt5_demo_cycle, "connect", lambda settings: None)
    monkeypatch.setattr(mt5_demo_cycle, "disconnect", lambda: None)
    monkeypatch.setattr(mt5_demo_cycle, "account_info", lambda: SimpleNamespace(equity=10_000))
    monkeypatch.setattr(mt5_demo_cycle, "bars", lambda symbol: pd.DataFrame({"close": [10.0] * 60}))
    monkeypatch.setattr(mt5_demo_cycle, "generate_mt5_signal", lambda symbol, frame: SimpleNamespace(action="BUY"))
    monkeypatch.setattr(mt5_demo_cycle, "calculate_volume", lambda *args: 0.1)
    monkeypatch.setattr(mt5_demo_cycle, "submit_demo_market_order", lambda *args: SimpleNamespace(retcode=10009))

    result = mt5_demo_cycle.run_demo_cycle("EURUSD", execute=True)
    assert result.submitted is True
    assert "Demo order submitted" in result.message
