"""Broker-neutral MT5 market-data service.

Execution is intentionally out of scope: this module only discovers symbols and
retrieves ticks/candles from the connected MT5 demo terminal.
"""

from dataclasses import dataclass
from datetime import datetime

import MetaTrader5 as mt5

from .mt5_client import bars, tick, available_instruments, select_symbol


@dataclass(frozen=True)
class MarketData:
    symbol: str
    timeframe: int
    candles: object


def discover_symbols(patterns: tuple[str, ...] = ("EURUSD", "XAUUSD", "BTCUSD", "ETHUSD")) -> dict[str, list[str]]:
    """Find broker symbols matching common Forex, gold and crypto names."""
    instruments = available_instruments()
    result: dict[str, list[str]] = {}
    for pattern in patterns:
        needle = pattern.upper()
        result[pattern] = [name for name in instruments if needle in name.upper()]
    return result


def get_tick(symbol: str):
    """Return the latest broker tick after ensuring the symbol is selected."""
    select_symbol(symbol)
    return tick(symbol)


def get_candles(symbol: str, timeframe=mt5.TIMEFRAME_M15, count: int = 500) -> MarketData:
    """Return recent OHLCV candles from MT5."""
    if count < 1:
        raise ValueError("count must be at least 1")
    select_symbol(symbol)
    return MarketData(symbol=symbol, timeframe=timeframe, candles=bars(symbol, timeframe, count))


def get_standard_market_snapshot(symbols: list[str], timeframe=mt5.TIMEFRAME_M15, count: int = 200) -> dict:
    """Collect ticks and candles while isolating failures per symbol."""
    snapshot = {}
    for symbol in symbols:
        try:
            snapshot[symbol] = {
                "tick": get_tick(symbol),
                "candles": get_candles(symbol, timeframe, count).candles,
            }
        except (ValueError, RuntimeError) as exc:
            snapshot[symbol] = {"error": str(exc)}
    return snapshot
