"""MT5-aware strategy adapter.

Keeps the existing deterministic strategy intact while converting MT5 candle
arrays into the DataFrame shape it expects. No orders are submitted here.
"""

import pandas as pd

from .strategy import Signal, generate_signal


def candles_to_dataframe(candles) -> pd.DataFrame:
    """Normalize MT5 copy_rates output for the strategy engine."""
    if candles is None:
        return pd.DataFrame()
    data = pd.DataFrame(candles)
    required = {"open", "high", "low", "close"}
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"MT5 candle data missing columns: {sorted(missing)}")
    return data


def generate_mt5_signal(
    symbol: str,
    candles,
    sma_period: int = 20,
    breakout_lookback: int = 10,
    min_return_pct: float = 2.0,
) -> Signal | None:
    """Generate a signal from MT5 candles using the existing strategy rules."""
    data = candles_to_dataframe(candles)
    return generate_signal(
        symbol=symbol,
        bars=data,
        sma_period=sma_period,
        breakout_lookback=breakout_lookback,
        min_return_pct=min_return_pct,
    )
