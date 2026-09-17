"""Safe paper-trading cycle: scan -> signal -> risk -> optional paper order."""

import json
from pathlib import Path

from .alpaca_client import create_trading_client
from .config import Settings
from .execution import submit_paper_buy
from .market_data import create_data_client, get_recent_daily_bars
from .strategy import generate_signal


ROOT = Path(__file__).resolve().parents[1]


def load_strategy():
    with open(ROOT / "config" / "strategy.json", encoding="utf-8") as f:
        return json.load(f)


def run_cycle(symbols: list[str], execute: bool = False):
    """Run one scan cycle. Orders require explicit execute=True and paper mode."""
    settings = Settings.from_env()
    trading = create_trading_client(settings)
    data = create_data_client(settings)
    strategy = load_strategy()
    account = trading.get_account()
    equity = float(account.equity)

    results = []
    for symbol in symbols:
        bars = get_recent_daily_bars(data, symbol, days=60)
        signal = generate_signal(
            symbol,
            bars,
            sma_period=int(strategy["sma_period"]),
            breakout_lookback=int(strategy["breakout_lookback"]),
            min_return_pct=float(strategy["min_return_pct"]),
        )
        if not signal:
            continue

        stop = signal.price * 0.98
        order_id = None
        if execute:
            order = submit_paper_buy(trading, settings, symbol, signal.price, stop, equity)
            order_id = str(order.id) if order else None
        results.append({"symbol": symbol, "action": signal.action, "price": signal.price, "order_id": order_id})

    return results
