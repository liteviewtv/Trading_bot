"""Continuous Telegram command worker."""

from __future__ import annotations

import time

from .telegram_polling import TelegramPollingBot


def run_forever(interval: float = 1.0) -> None:
    bot = TelegramPollingBot()
    if not bot.configured:
        raise RuntimeError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are required")
    while True:
        try:
            bot.poll_once()
        except Exception as exc:
            print(f"Telegram worker error: {exc}", flush=True)
            time.sleep(max(interval, 2.0))


if __name__ == "__main__":
    run_forever()
