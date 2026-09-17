"""Small monitoring helpers for account and bot events."""

from .notifications import send_telegram
from .trade_store import TradeStore


def notify_event(store: TradeStore, level: str, event: str, details: str = "") -> bool:
    store.record_event(level, event, details)
    return send_telegram(f"Trading Bot [{level}]\n{event}\n{details}".strip())
