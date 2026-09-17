from types import SimpleNamespace

from src import mt5_auto_cycle


def test_auto_cycle_never_executes_when_disabled(monkeypatch):
    monkeypatch.setattr(mt5_auto_cycle, "scan_assets", lambda assets: [
        SimpleNamespace(requested="EURUSD", symbol="EURUSD", signal=SimpleNamespace(action="BUY"), error=None),
        SimpleNamespace(requested="XAUUSD", symbol="XAUUSDm", signal=SimpleNamespace(action="SELL"), error=None),
    ])
    calls = []
    monkeypatch.setattr(mt5_auto_cycle, "run_demo_cycle", lambda *args, **kwargs: calls.append(args))

    result = mt5_auto_cycle.run_auto_demo_cycle(execute=False)
    assert result.executed == []
    assert len(calls) == 0
    assert len(result.skipped) == 2


def test_auto_cycle_enforces_order_limit(monkeypatch):
    monkeypatch.setattr(mt5_auto_cycle, "scan_assets", lambda assets: [
        SimpleNamespace(requested="EURUSD", symbol="EURUSD", signal=SimpleNamespace(action="BUY"), error=None),
        SimpleNamespace(requested="GBPUSD", symbol="GBPUSD", signal=SimpleNamespace(action="BUY"), error=None),
        SimpleNamespace(requested="XAUUSD", symbol="XAUUSDm", signal=SimpleNamespace(action="SELL"), error=None),
    ])
    monkeypatch.setattr(mt5_auto_cycle, "run_demo_cycle", lambda symbol, execute=True: SimpleNamespace(symbol=symbol, submitted=True))

    result = mt5_auto_cycle.run_auto_demo_cycle(execute=True, max_orders=2)
    assert len(result.executed) == 2
    assert any("order limit reached" in item for item in result.skipped)
