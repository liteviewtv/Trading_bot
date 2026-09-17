"""Telegram command helpers for paper-trading status and controls."""

from __future__ import annotations


def status_message(summary: dict) -> str:
    trades = int(summary.get("trades", 0))
    wins = int(summary.get("wins", 0))
    losses = int(summary.get("losses", 0))
    win_rate = (wins / trades * 100) if trades else 0.0
    return (
        "📊 PAPER TRADING STATUS\n"
        f"Trades: {trades}\n"
        f"Wins: {wins}\n"
        f"Losses: {losses}\n"
        f"Win rate: {win_rate:.1f}%\n"
        f"Total return: {float(summary.get('total_return_pct', 0)):.2f}%\n"
        f"Max drawdown: {float(summary.get('max_drawdown_pct', 0)):.2f}%\n"
        f"Avg AI confidence: {float(summary.get('average_confidence', 0)):.1%}"
    )


def handle_command(command: str, summary: dict, control=None, positions=None) -> str | None:
    command = command.strip().split()[0].lower() if command.strip() else ""
    if command.startswith("/status"):
        return status_message(summary)
    if control is not None and command in {"/pause", "/resume", "/positions"}:
        return control.handle(command, positions)
    return None
