"""Initial scanner: simple liquidity/price filter for later strategy work."""

from typing import Iterable

import pandas as pd

from .market_data import get_recent_daily_bars


def scan_symbols(client, symbols: Iterable[str], min_price: float = 5.0, min_avg_volume: int = 500_000) -> pd.DataFrame:
    """Build a basic candidate list from recent daily data.

    This is a scanner only; it does not generate orders.
    """
    rows = []
    for symbol in symbols:
        try:
            bars = get_recent_daily_bars(client, symbol, days=30)
            if bars.empty:
                continue
            if isinstance(bars.index, pd.MultiIndex):
                bars = bars.xs(symbol, level="symbol")
            last = bars.iloc[-1]
            avg_volume = float(bars["volume"].tail(20).mean())
            price = float(last["close"])
            if price >= min_price and avg_volume >= min_avg_volume:
                rows.append({"symbol": symbol, "price": price, "avg_volume": avg_volume})
        except Exception:
            # One bad symbol must not stop the complete scan.
            continue

    return pd.DataFrame(rows, columns=["symbol", "price", "avg_volume"])
