from types import SimpleNamespace

from src import mt5_auto_cycle
from src.telegram_control import DemoControl


def test_paused_control_blocks_new_demo_trades(monkeypatch):
    control = DemoControl()
    control.paused = True
    monkeypatch.setattr(mt5_auto_cycle, "scan_assets", lambda assets: [
        SimpleNamespace(requested="EURUSD", symbol="EURUSD", signal=SimpleNamespace(action="BUY"), error=None)
    ])
    called = []
    monkeypatch.setattr(mt5_auto_cycle, "run_demo_cycle", lambda *args, **kwargs: called.append(True))
    result = mt5_auto_cycle.run_auto_demo_cycle(execute=True, control=control)
    assert result.executed == []
    assert "demo trading paused" in result.skipped
    assert called == []


def test_help_command_lists_controls():
    from src.telegram_control import DemoControl
    text = DemoControl().handle("/help")
    assert "/pause" in text
    assert "/resume" in text
    assert "/positions" in text
    assert "/status" in text
