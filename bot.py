"""Long-running paper-trading entry point with Telegram command polling."""

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
    cycle = 0

    while max_cycles == 0 or cycle < max_cycles:
        cycle += 1
        try:
            if telegram_enabled:
                telegram.poll_once()

            cycle_execute = execute and not telegram.control.paused
            if execute and telegram.control.paused:
                logging.info("Paper trading paused via Telegram; skipping new orders")
                results = []
            else:
                results = run_cycle(symbols, execute=cycle_execute)

            logging.info("Cycle %d completed: %d signal(s)", cycle, len(results))
            for result in results:
                logging.info("%s", result)
        except Exception:
            logging.exception("Trading cycle failed")

        if max_cycles == 0:
            time.sleep(max(1, int(os.getenv("TELEGRAM_POLL_INTERVAL_SECONDS", "10"))))
        elif cycle < max_cycles:
            time.sleep(interval)


if __name__ == "__main__":
    main()
