from types import SimpleNamespace

from src.telegram_commands import handle_command
from src.telegram_control import DemoControl


def test_controls_route_through_command_handler():
    control = DemoControl()
    assert "paused" in handle_command("/pause", {}, control).lower()
    assert control.paused
    assert "resumed" in handle_command("/resume", {}, control).lower()
    assert not control.paused
    text = handle_command("/positions", {}, control, [SimpleNamespace(symbol="EURUSD", action="BUY", pnl_pct=1.0)])
    assert "EURUSD BUY" in text
