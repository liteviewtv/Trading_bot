"""Scheduled paper-trading entry point with explicit safety gates."""

import json
import logging
import time
from pathlib import Path

from src.runner import run_cycle

ROOT = Path(__file__).resolve().parent
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def load_universe():
    with open(ROOT / "config" / "universe.json", encoding="utf-8") as f:
        return json.load(f)


def main():
    cfg = load_universe()
    symbols = cfg["symbols"]
    execute = bool(cfg.get("execute_paper_orders", False))
    max_cycles = int(__import__("os").getenv("BOT_MAX_CYCLES", "1"))
    interval = int(__import__("os").getenv("BOT_INTERVAL_SECONDS", "300"))

    for cycle in range(max_cycles):
        try:
            results = run_cycle(symbols, execute=execute)
            logging.info("Cycle %d completed: %d signal(s)", cycle + 1, len(results))
            for result in results:
                logging.info("%s", result)
        except Exception:
            logging.exception("Trading cycle failed")
        if cycle + 1 < max_cycles:
            time.sleep(interval)


if __name__ == "__main__":
    main()
