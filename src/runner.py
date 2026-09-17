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


def load_universe():
    with open(ROOT / "config" / "universe.json", encoding="utf-8") as f:
        return json.load(f)


def run_cycle(symbols: list[str], execute: bool = False):
    """Run one cycle with position and per-cycle trade limits."""
    settings = Settings.from_env()
    trading = create_trading_client(settings)
    data = create_data_client(settings)
    strategy = load_strategy()
    universe = load_universe()
    account = trading.get_account()
    equity = float(account.equity)
    open_positions = len(trading.get_all_positions())
    trades_this_cycle = 0
    results = []

    for symbol in symbols:
        if trades_this_cycle >= int(universe["max_trades_per_cycle"]):
            break
        bars = get_recent_daily_bars(data, symbol, days=60)
        signal = generate_signal(
            symbol, bars,
            sma_period=int(strategy["sma_period"]),
            breakout_lookback=int(strategy["breakout_lookback"]),
            min_return_pct=float(strategy["min_return_pct"]),
        )
        if not signal:
            continue

        stop = signal.price * (1 - float(universe["stop_loss_pct"]) / 100)
        order_id = None
        if execute and universe.get("execute_paper_orders", False):
            order = submit_paper_buy(
                trading, settings, symbol, signal.price, stop, equity,
                open_positions=open_positions,
                trades_this_cycle=trades_this_cycle,
                max_concurrent_positions=int(universe["max_concurrent_positions"]),
                max_trades_per_cycle=int(universe["max_trades_per_cycle"]),
            )
            if order:
                order_id = str(order.id)
                open_positions += 1
                trades_this_cycle += 1
        results.append({"symbol": symbol, "action": signal.action, "price": signal.price, "order_id": order_id})

    return results
