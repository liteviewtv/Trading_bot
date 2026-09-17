"""Telegram notifications via the Bot HTTP API."""

import os
from urllib.parse import quote

import requests


def send_telegram(message: str) -> bool:
    """Send a Telegram message when credentials are configured.

    Missing credentials are treated as disabled notifications rather than errors.
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        return False

    url = f"https://api.telegram.org/bot{quote(token, safe='')}/sendMessage"
    response = requests.post(url, json={"chat_id": chat_id, "text": message}, timeout=15)
    response.raise_for_status()
    return True
