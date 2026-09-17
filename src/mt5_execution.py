"""Demo-only MetaTrader 5 order execution helpers.

This module deliberately refuses live trading. It converts a validated signal
into an MT5 market order with broker-aware volume normalization and SL/TP.
"""

from __future__ import annotations

import math

import MetaTrader5 as mt5

from .mt5_client import select_symbol


def _require_demo_account():
    """Refuse execution unless the connected MT5 account is a demo account."""
    account = mt5.account_info()
    if account is None:
        raise RuntimeError("MT5 account information is unavailable")
    trade_mode = getattr(account, "trade_mode", None)
    demo_mode = getattr(mt5, "ACCOUNT_TRADE_MODE_DEMO", 0)
    if trade_mode != demo_mode:
        raise RuntimeError("MT5 execution is restricted to demo accounts")
    return account


def _normalize_volume(info, volume: float) -> float:
    step = float(info.volume_step or 0.01)
    minimum = float(info.volume_min or step)
    maximum = float(info.volume_max or volume)
    if volume < minimum:
        return 0.0
    steps = math.floor(volume / step)
    normalized = steps * step
    if normalized < minimum:
        return 0.0
    return min(normalized, maximum)


def calculate_volume(
    symbol: str,
    entry_price: float,
    stop_price: float,
    equity: float,
    risk_fraction: float = 0.01,
) -> float:
    """Estimate MT5 lots from account risk and broker contract metadata."""
    if equity <= 0 or entry_price <= 0 or stop_price <= 0 or entry_price == stop_price:
        return 0.0
    info = select_symbol(symbol)
    risk_budget = equity * risk_fraction
    profit = mt5.order_calc_profit(mt5.ORDER_TYPE_BUY, symbol, 1.0, entry_price, stop_price)
    if profit is None or float(profit) == 0:
        return 0.0
    raw_volume = risk_budget / abs(float(profit))
    return _normalize_volume(info, raw_volume)


def submit_demo_market_order(
    symbol: str,
    side: str,
    volume: float,
    stop_loss: float,
    take_profit: float,
    deviation: int = 20,
    magic: int = 260917,
):
    """Submit a market order only through a connected MT5 demo terminal."""
    _require_demo_account()
    info = select_symbol(symbol)
    if volume <= 0 or stop_loss <= 0 or take_profit <= 0:
        raise ValueError("Invalid order parameters")

    side = side.upper()
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        raise RuntimeError(f"No current tick available for {symbol}")
    if side == "BUY":
        order_type = mt5.ORDER_TYPE_BUY
        price = float(tick.ask)
    elif side == "SELL":
        order_type = mt5.ORDER_TYPE_SELL
        price = float(tick.bid)
    else:
        raise ValueError("side must be BUY or SELL")

    volume = _normalize_volume(info, volume)
    if volume <= 0:
        raise ValueError("Volume is below the broker minimum")

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": volume,
        "type": order_type,
        "price": price,
        "sl": float(stop_loss),
        "tp": float(take_profit),
        "deviation": deviation,
        "magic": magic,
        "comment": "Trading_bot demo",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": info.filling_mode,
    }
    return mt5.order_send(request)
