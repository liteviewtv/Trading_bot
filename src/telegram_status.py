"""Telegram /status polling handler backed by the paper-trade journal."""

from __future__ import annotations

import json
from pathlib import Path

from .paper_tracker import PaperTrade, summarize_paper_trades
from .telegram_commands import handle_command
from .telegram_notify import TelegramNotifier


def load_paper_trades(path) -> list[PaperTrade]:
    target = Path(path)
    if not target.exists():
        return []
    trades = []
    for line in target.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        record = json.loads(line)
        if record.get("type") != "paper_outcome":
            continue
        trades.append(PaperTrade(
            symbol=str(record.get("symbol", "")),
            action=str(record.get("decision", "HOLD")),
            entry=float(record.get("entry", 0)),
            exit=float(record.get("exit", 0)),
            confidence=float(record.get("confidence", 0)),
        ))
    return trades


def status_for_journal(path) -> str:
    summary = summarize_paper_trades(load_paper_trades(path))
    return handle_command("/status", summary) or ""


def respond_to_update(update: dict, *, journal_path, notifier: TelegramNotifier | None = None) -> bool:
    message = update.get("message") or {}
    text = message.get("text", "")
    if not text.lower().startswith("/status"):
        return False
    reply = status_for_journal(journal_path)
    (notifier or TelegramNotifier()).send(reply)
    return True
