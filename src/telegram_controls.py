"""Small Telegram command handler for bot status and summaries."""

import os
import requests

from .trade_store import TradeStore


def send_message(text: str) -> bool:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        return False
    r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json={"chat_id": chat_id, "text": text}, timeout=15)
    r.raise_for_status()
    return True


def daily_summary(store: TradeStore) -> str:
    with store._connect() as db:
        row = db.execute("SELECT COALESCE(SUM(pnl),0), COUNT(*), COALESCE(SUM(CASE WHEN pnl > 0 THEN 1 ELSE 0 END),0) FROM trades WHERE status='CLOSED' AND date(closed_at)=date('now')").fetchone()
    pnl, trades, wins = row
    win_rate = (wins / trades * 100) if trades else 0
    return f"Daily Trading Bot Summary\nClosed trades: {trades}\nWins: {wins}\nWin rate: {win_rate:.1f}%\nP&L: ${pnl:.2f}"
