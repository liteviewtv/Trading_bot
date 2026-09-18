"""Long-running Alpaca paper-trading bot entry point with Telegram control."""
import json
import logging
import os
import time
from pathlib import Path
from src.alpaca_auto_cycle import run_auto_demo_cycle
from src.alpaca_client import account
from src.telegram_polling import TelegramPollingBot

ROOT = Path(__file__).resolve().parent
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

def load_universe():
    with open(ROOT / "config" / "universe.json", encoding="utf-8") as f:
        return json.load(f)

def main():
    cfg = load_universe()
    assets = tuple(cfg.get("symbols") or cfg.get("assets") or ())
    execute = bool(cfg.get("execute_paper_orders", False))
    max_cycles = int(os.getenv("BOT_MAX_CYCLES", "1"))
    interval = int(os.getenv("BOT_INTERVAL_SECONDS", "300"))
    max_orders = int(cfg.get("max_trades_per_cycle", 2))
    max_positions = int(cfg.get("max_concurrent_positions", 5))
    telegram = TelegramPollingBot()
    if telegram.configured:
        try:
            telegram.notifier.send("🟢 ALPACA PAPER BOT ONLINE\nExecution: Alpaca REST API\nTelegram polling enabled.")
        except Exception:
            logging.exception("Unable to send Telegram startup notification")
    if execute:
        account()
    cycle = 0
    while max_cycles == 0 or cycle < max_cycles:
        cycle += 1
        try:
            if telegram.configured:
                telegram.poll_once()
            result = run_auto_demo_cycle(
                assets=assets,
                execute=execute and not telegram.control.paused,
                max_orders=max_orders,
                max_open_positions=max_positions,
                control=telegram.control,
            )
            logging.info("Cycle %d: scanned=%d executed=%d skipped=%d", cycle, len(result.scanned), len(result.executed), len(result.skipped))
        except Exception:
            logging.exception("Alpaca paper cycle failed")
        if max_cycles == 0:
            time.sleep(max(1, int(os.getenv("TELEGRAM_POLL_INTERVAL_SECONDS", "10"))))
        elif cycle < max_cycles:
            time.sleep(interval)

if __name__ == "__main__":
    main()
