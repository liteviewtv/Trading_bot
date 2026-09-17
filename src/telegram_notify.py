"""Small Telegram Bot API notification client.

Notifications are outbound only; this module has no trading or broker access.
"""

from __future__ import annotations

import json
import os
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class TelegramNotifier:
    def __init__(self, token: str | None = None, chat_id: str | None = None, timeout: float = 10.0):
        self.token = token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
        self.timeout = timeout

    @property
    def configured(self) -> bool:
        return bool(self.token and self.chat_id)

    def send(self, message: str) -> bool:
        if not self.configured:
            return False
        if not message or len(message) > 4096:
            raise ValueError("Telegram message must contain 1-4096 characters")
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        body = urlencode({"chat_id": self.chat_id, "text": message}).encode()
        request = Request(url, data=body, method="POST")
        with urlopen(request, timeout=self.timeout) as response:
            result = json.loads(response.read().decode())
        if not result.get("ok"):
            raise RuntimeError("Telegram API rejected notification")
        return True

    def signal(self, symbol: str, action: str, confidence: float, reason: str = "") -> bool:
        text = f"🤖 AI SIGNAL\nSymbol: {symbol}\nAction: {action}\nConfidence: {confidence:.0%}"
        if reason:
            text += f"\nReason: {reason}"
        return self.send(text)

    def event(self, title: str, details: str = "") -> bool:
        text = title if not details else f"{title}\n{details}"
        return self.send(text)
