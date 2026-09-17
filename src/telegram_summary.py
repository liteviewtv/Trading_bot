"""Format paper-trading statistics for Telegram."""

from __future__ import annotations


def format_performance_summary(stats: dict) -> str:
    trades = int(stats.get("trades", 0))
    wins = int(stats.get("wins", 0))
    losses = int(stats.get("losses", 0))
    win_rate = wins / trades * 100 if trades else 0.0
    return (
        "📊 PAPER TRADING SUMMARY\n"
        f"Trades: {trades}\n"
        f"Wins: {wins}\n"
        f"Losses: {losses}\n"
        f"Win rate: {win_rate:.1f}%\n"
        f"Total return: {float(stats.get('total_return_pct', 0.0)):.2f}%\n"
        f"Average return: {float(stats.get('average_return_pct', 0.0)):.2f}%\n"
        f"Max drawdown: {float(stats.get('max_drawdown_pct', 0.0)):.2f}%\n"
        f"Average AI confidence: {float(stats.get('average_confidence', 0.0)):.1%}"
    )


def send_performance_summary(notifier, stats: dict) -> bool:
    """Send the current paper-trading summary through an existing notifier."""
    return notifier.send(format_performance_summary(stats))
