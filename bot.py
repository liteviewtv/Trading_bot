"""Long-running Alpaca paper-trading bot entry point with Telegram control."""
import json
import logging
import os
import time
from pathlib import Path
from src.alpaca_auto_cycle import run_auto_demo_cycle
from src.alpaca_client import account, crypto_universe
from src.telegram_polling import TelegramPollingBot

ROOT = Path(__file__).resolve().parent
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

def load_universe():
    with open(ROOT / "config" / "universe.json", encoding="utf-8") as f:
        return json.load(f)

def main():
    cfg = load_universe()
    dynamic_crypto = bool(cfg.get("dynamic_crypto_universe", False))
    if dynamic_crypto:
        try:
            assets = tuple(crypto_universe(cfg.get("exclude_symbols", [])))
            logging.info("Dynamic Alpaca crypto universe loaded: %d active tradable USD pairs", len(assets))
        except Exception:
            logging.exception("Unable to load dynamic Alpaca crypto universe")
            assets = ()
    else:
        assets = tuple(cfg.get("symbols") or cfg.get("assets") or ())
    execute = bool(cfg.get("execute_paper_orders", False))
    max_cycles = int(os.getenv("BOT_MAX_CYCLES", "1"))
    interval = int(os.getenv("BOT_INTERVAL_SECONDS", "300"))
    max_orders = int(cfg.get("max_trades_per_cycle", 2))
    max_positions = int(cfg.get("max_concurrent_positions", 5))
    min_return_pct = float(cfg.get("min_return_pct", 0.1))
    sma_period = int(cfg.get("sma_period", 50))
    breakout_lookback = int(cfg.get("breakout_lookback", 20))
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
            if dynamic_crypto:
                assets = tuple(crypto_universe(cfg.get("exclude_symbols", [])))
                logging.info("Cycle %d dynamic crypto universe: %d active tradable USD pairs", cycle, len(assets))
            result = run_auto_demo_cycle(
                assets=assets,
                execute=execute and not telegram.control.paused,
                max_orders=max_orders,
                max_open_positions=max_positions,
                min_return_pct=min_return_pct,
                sma_period=sma_period,
                breakout_lookback=breakout_lookback,
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
