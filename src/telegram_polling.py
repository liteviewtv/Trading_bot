"""Long-polling Telegram command worker for the demo trading bot."""

from __future__ import annotations

import json
import os
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .paper_tracker import PaperTrade, summarize_paper_trades
from .telegram_commands import handle_command
from .telegram_control import DemoControl
from .telegram_notify import TelegramNotifier


class TelegramPollingBot:
    def __init__(self, token=None, chat_id=None, control=None, timeout=25):
        self.token = token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = str(chat_id or os.getenv("TELEGRAM_CHAT_ID")) if (chat_id or os.getenv("TELEGRAM_CHAT_ID")) else None
        self.timeout = timeout
        self.control = control or DemoControl()
        self.offset = 0
        self.notifier = TelegramNotifier(self.token, self.chat_id)

    @property
    def configured(self):
        return bool(self.token and self.chat_id)

    def _request(self, method, params=None):
        url = f"https://api.telegram.org/bot{self.token}/{method}"
        body = urlencode(params or {}).encode()
        request = Request(url, data=body, method="POST")
        with urlopen(request, timeout=self.timeout + 5) as response:
            result = json.loads(response.read().decode())
        if not result.get("ok"):
            raise RuntimeError(f"Telegram API rejected {method}")
        return result.get("result", [])

    def poll_once(self, summary=None, positions=None):
        if not self.configured:
            return 0
        updates = self._request("getUpdates", {"offset": self.offset, "timeout": self.timeout})
        handled = 0
        summary = summary or summarize_paper_trades([])
        for update in updates:
            self.offset = max(self.offset, int(update["update_id"]) + 1)
            message = update.get("message") or {}
            chat = message.get("chat") or {}
            if str(chat.get("id")) != self.chat_id:
                continue
            text = message.get("text") or ""
            reply = handle_command(text, summary, self.control, positions)
            if reply:
                self.notifier.send(reply)
            handled += 1
        return handled
