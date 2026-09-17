from src.telegram_summary import format_performance_summary


def test_format_performance_summary():
    text = format_performance_summary({
        "trades": 10,
        "wins": 6,
        "losses": 4,
        "total_return_pct": 8.5,
        "average_return_pct": 0.85,
        "max_drawdown_pct": 3.2,
        "average_confidence": 0.74,
    })
    assert "Trades: 10" in text
    assert "Win rate: 60.0%" in text
    assert "Total return: 8.50%" in text
    assert "Max drawdown: 3.20%" in text
    assert "Average AI confidence: 74.0%" in text
