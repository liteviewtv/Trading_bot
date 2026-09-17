from src.telegram_commands import handle_command, status_message


def test_status_message():
    text = status_message({"trades": 4, "wins": 3, "losses": 1, "total_return_pct": 2.5, "max_drawdown_pct": 1.2, "average_confidence": 0.75})
    assert "PAPER TRADING STATUS" in text
    assert "Win rate: 75.0%" in text
    assert "Total return: 2.50%" in text


def test_status_command():
    assert "PAPER TRADING STATUS" in handle_command("/status", {"trades": 0})
    assert handle_command("/help", {"trades": 0}) is None
