"""Long-polling Telegram command worker for the demo trading bot."""

from __future__ import annotations

import json
import logging
import os
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .paper_tracker import summarize_paper_trades
from .telegram_commands import handle_command
from .telegram_control import DemoControl
from .telegram_notify import TelegramNotifier

log = logging.getLogger(__name__)


class TelegramPollingBot:
    def __init__(self, token=None, chat_id=None, control=None, timeout=25):
        self.token = token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = str(chat_id or os.getenv("TELEGRAM_CHAT_ID")) if (chat_id or os.getenv("TELEGRAM_CHAT_ID")) else None
        self.timeout = timeout
        self.control = control or DemoControl()
        self.offset = 0
        self.notifier = TelegramNotifier(self.token, self.chat_id)
        self._started = False

    @property
    def configured(self):
        return bool(self.token and self.chat_id)

    def _request(self, method, params=None):
        url = f"https://api.telegram.org/bot{self.token}/{method}"
        body = urlencode(params or {}).encode()
        request = Request(url, data=body, method="POST")
        try:
            with urlopen(request, timeout=self.timeout + 5) as response:
                result = json.loads(response.read().decode())
        except HTTPError as exc:
            if exc.code == 409 and method == "getUpdates":
                raise RuntimeError("Telegram polling conflict: another poller or webhook is active") from exc
            raise
        if not result.get("ok"):
            raise RuntimeError(f"Telegram API rejected {method}: {result.get('description', 'unknown error')}")
        return result.get("result", [])

    def start(self):
        if not self.configured or self._started:
            return
        self._request("deleteWebhook", {"drop_pending_updates": "false"})
        self._started = True
        log.info("Telegram polling initialized successfully for configured chat")

    def poll_once(self, summary=None, positions=None):
        if not self.configured:
            log.warning("Telegram polling disabled: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is missing")
            return 0
        try:
            self.start()
            updates = self._request("getUpdates", {"offset": self.offset, "timeout": self.timeout})
        except RuntimeError as exc:
            if str(exc).startswith("Telegram polling conflict:"):
                self._started = False
                log.error("Telegram polling conflict: another process/webhook is consuming updates")
                return 0
            log.exception("Telegram polling request failed")
            return 0
        handled = 0
        summary = summary or summarize_paper_trades([])
        for update in updates:
            self.offset = max(self.offset, int(update["update_id"]) + 1)
            message = update.get("message") or {}
            chat = message.get("chat") or {}
            if str(chat.get("id")) != self.chat_id:
                continue
            text = message.get("text") or ""
            log.info("Telegram command received: %s", text.split()[0] if text else "<empty>")
            reply = handle_command(text, summary, self.control, positions)
            if reply:
                self.notifier.send(reply)
            handled += 1
        if updates:
            log.info("Telegram polling handled %d update(s)", handled)
        return handled
