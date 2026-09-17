"""Scheduled paper-trading entry point with explicit safety gates."""

import json
import logging
import os
import time
from pathlib import Path

from src.runner import run_cycle
from src.telegram_polling import TelegramPollingBot

ROOT = Path(__file__).resolve().parent
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def load_universe():
    with open(ROOT / "config" / "universe.json", encoding="utf-8") as f:
        return json.load(f)


def main():
    cfg = load_universe()
    symbols = cfg["symbols"]
    execute = bool(cfg.get("execute_paper_orders", False))
    max_cycles = int(os.getenv("BOT_MAX_CYCLES", "1"))
    interval = int(os.getenv("BOT_INTERVAL_SECONDS", "300"))
    telegram = TelegramPollingBot()
    telegram_enabled = telegram.configured

    for cycle in range(max_cycles):
        try:
            if telegram_enabled:
                telegram.poll_once()

            # A Telegram /pause command updates the same control object used by
            # the command handler. Do not open new paper trades while paused.
            cycle_execute = execute and not telegram.control.paused
            if execute and telegram.control.paused:
                logging.info("Paper trading paused via Telegram; skipping new orders")
                results = []
            else:
                results = run_cycle(symbols, execute=cycle_execute)

            logging.info("Cycle %d completed: %d signal(s)", cycle + 1, len(results))
            for result in results:
                logging.info("%s", result)

            if telegram_enabled:
                telegram.poll_once()
        except Exception:
            logging.exception("Trading cycle failed")
        if cycle + 1 < max_cycles:
            time.sleep(interval)


if __name__ == "__main__":
    main()
