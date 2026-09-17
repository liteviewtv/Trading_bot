"""Deterministic momentum signal engine.

Signals are informational only; this module never submits orders.
"""

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class Signal:
    symbol: str
    action: str
    price: float
    reason: str


def generate_signal(symbol: str, bars: pd.DataFrame, sma_period: int = 20,
                    breakout_lookback: int = 10, min_return_pct: float = 2.0):
    """Generate a long signal when price has momentum and breaks recent highs."""
    if len(bars) < max(sma_period, breakout_lookback) + 1:
        return None

    data = bars.copy()
    data["sma"] = data["close"].rolling(sma_period).mean()
    previous = data.iloc[-2]
    latest = data.iloc[-1]
    prior_high = float(data["high"].iloc[-breakout_lookback-1:-1].max())
    day_return_pct = (float(latest["close"]) / float(previous["close"]) - 1) * 100

    if (
        float(latest["close"]) > float(latest["sma"])
        and float(latest["close"]) > prior_high
        and day_return_pct >= min_return_pct
    ):
        return Signal(
            symbol=symbol,
            action="BUY",
            price=float(latest["close"]),
            reason=f"Close above SMA{ sma_period }, {breakout_lookback}-day breakout, "
                   f"daily return {day_return_pct:.2f}%",
        )

    return None
