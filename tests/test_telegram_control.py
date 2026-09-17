from types import SimpleNamespace

from src.telegram_control import DemoControl


def test_pause_and_resume():
    control = DemoControl()
    assert control.handle("/pause") == "⏸️ Demo trading paused."
    assert control.paused
    assert control.handle("/resume") == "▶️ Demo trading resumed."
    assert not control.paused


def test_positions():
    control = DemoControl()
    assert "No open positions" in control.handle("/positions")
    position = SimpleNamespace(symbol="EURUSD", action="BUY", pnl_pct=1.25)
    text = control.handle("/positions", [position])
    assert "EURUSD BUY" in text
    assert "1.25%" in text
