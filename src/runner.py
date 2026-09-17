"""Safe paper-trading cycle with position monitoring and journaling."""

import json
from pathlib import Path

from .alpaca_client import create_trading_client
from .config import Settings
from .execution import submit_paper_buy
from .market_data import create_data_client, get_recent_daily_bars
from .position_manager import monitor_positions
from .strategy import generate_signal
from .telegram_notify import TelegramNotifier
from .trade_store import TradeStore

ROOT = Path(__file__).resolve().parents[1]


def load_json(name):
    with open(ROOT / "config" / name, encoding="utf-8") as f:
        return json.load(f)


def run_cycle(symbols: list[str], execute: bool = False):
    """Run monitoring, scanning, risk checks, paper execution and journaling."""
    settings = Settings.from_env()
    trading = create_trading_client(settings)
    data = create_data_client(settings)
    strategy = load_json("strategy.json")
    universe = load_json("universe.json")
    store = TradeStore()
    telegram = TelegramNotifier()

    if execute and universe.get("execute_paper_orders", False):
        for action in monitor_positions(
            trading,
            stop_loss_pct=float(universe["stop_loss_pct"]) / 100,
            take_profit_pct=float(universe["take_profit_pct"]) / 100,
        ):
            store.record_event("INFO", "POSITION_EXIT", str(action))
            if telegram.configured:
                telegram.event("📤 POSITION EXIT", str(action))

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

        if telegram.configured:
            telegram.event(
                "🤖 AI/PAPER SIGNAL",
                f"Symbol: {signal.symbol}\nAction: {signal.action}\nPrice: {signal.price:.6f}\nReason: {signal.reason}",
            )

        stop = signal.price * (1 - float(universe["stop_loss_pct"]) / 100)
        order_id = None
        qty = 0
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
                qty = int(float(order.qty))
                open_positions += 1
                trades_this_cycle += 1
                store.record_trade(symbol, "BUY", qty, "SUBMITTED", signal.price, order_id, signal.reason)
                if telegram.configured:
                    telegram.event("🟢 PAPER ORDER SUBMITTED", f"Symbol: {symbol}\nSide: BUY\nQuantity: {qty}\nPrice: {signal.price:.6f}\nOrder ID: {order_id}")
            elif telegram.configured:
                telegram.event("⛔ PAPER ORDER BLOCKED", f"Symbol: {symbol}\nSignal: {signal.action}\nPrice: {signal.price:.6f}\nRisk/position/order limit prevented submission.")

        results.append({"symbol": symbol, "action": signal.action, "price": signal.price, "order_id": order_id})

    store.record_event("INFO", "CYCLE_COMPLETE", f"signals={len(results)} orders={trades_this_cycle}")
    if telegram.configured:
        telegram.event("🔄 PAPER CYCLE COMPLETE", f"Signals: {len(results)}\nOrders submitted: {trades_this_cycle}")
    return results
