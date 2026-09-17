from types import ModuleType, SimpleNamespace

import pandas as pd

from src import mt5_demo_cycle


def fake_modules(monkeypatch, order_submitter):
    client = ModuleType("src.mt5_client")
    client.MT5Settings = SimpleNamespace(from_env=lambda: object())
    client.connect = lambda settings: None
    client.disconnect = lambda: None
    client.account_info = lambda: SimpleNamespace(equity=10_000)
    client.bars = lambda symbol: pd.DataFrame({"close": [10.0] * 60})

    execution = ModuleType("src.mt5_execution")
    execution.calculate_volume = lambda *args: 0.1
    execution.submit_demo_market_order = order_submitter

    strategy = ModuleType("src.mt5_strategy")
    strategy.generate_mt5_signal = lambda symbol, frame: SimpleNamespace(action="BUY")

    monkeypatch.setitem(__import__("sys").modules, "src.mt5_client", client)
    monkeypatch.setitem(__import__("sys").modules, "src.mt5_execution", execution)
    monkeypatch.setitem(__import__("sys").modules, "src.mt5_strategy", strategy)


def test_cycle_does_not_execute_by_default(monkeypatch):
    called = {"order": False}

    def fail_if_called(*args, **kwargs):
        called["order"] = True
        raise AssertionError("demo order must not be submitted when execute=False")

    fake_modules(monkeypatch, fail_if_called)
    result = mt5_demo_cycle.run_demo_cycle("EURUSD")

    assert result.submitted is False
    assert called["order"] is False
    assert "execution disabled" in result.message


def test_cycle_submits_when_explicitly_enabled(monkeypatch):
    fake_modules(monkeypatch, lambda *args: SimpleNamespace(retcode=10009))

    result = mt5_demo_cycle.run_demo_cycle("EURUSD", execute=True)
    assert result.submitted is True
    assert "Demo order submitted" in result.message
