"""Deterministic momentum/breakout signal engine.

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
    """Generate a BUY or SELL signal from momentum and recent breakouts."""
    if len(bars) < max(sma_period, breakout_lookback) + 1:
        return None

    if min_return_pct < 0:
        raise ValueError("min_return_pct must be non-negative")

    data = bars.copy()
    data["sma"] = data["close"].rolling(sma_period).mean()
    previous = data.iloc[-2]
    latest = data.iloc[-1]
    prior_high = float(data["high"].iloc[-breakout_lookback-1:-1].max())
    prior_low = float(data["low"].iloc[-breakout_lookback-1:-1].min())
    day_return_pct = (float(latest["close"]) / float(previous["close"]) - 1) * 100
    close = float(latest["close"])
    sma = float(latest["sma"])

    if close > sma and close >= sma * 1.005 and close > prior_high and day_return_pct >= min_return_pct:
        return Signal(
            symbol=symbol,
            action="BUY",
            price=close,
            reason=f"Close above SMA{sma_period}, {breakout_lookback}-period high breakout, "
                   f"return {day_return_pct:.2f}%, SMA distance {(close / sma - 1) * 100:.2f}%",
        )

    if close < sma and close < prior_low and day_return_pct <= -min_return_pct:
        return Signal(
            symbol=symbol,
            action="SELL",
            price=close,
            reason=f"Close below SMA{sma_period}, {breakout_lookback}-period low breakout, "
                   f"return {day_return_pct:.2f}%",
        )

    return None


def diagnose_signal(symbol: str, bars: pd.DataFrame, sma_period: int = 20,
                    breakout_lookback: int = 10, min_return_pct: float = 2.0) -> str:
    """Return a concise explanation of why the latest bar did not signal."""
    if len(bars) < max(sma_period, breakout_lookback) + 1:
        return f"insufficient bars ({len(bars)}/{max(sma_period, breakout_lookback) + 1})"

    data = bars.copy()
    data["sma"] = data["close"].rolling(sma_period).mean()
    previous = data.iloc[-2]
    latest = data.iloc[-1]
    prior_high = float(data["high"].iloc[-breakout_lookback-1:-1].max())
    prior_low = float(data["low"].iloc[-breakout_lookback-1:-1].min())
    day_return_pct = (float(latest["close"]) / float(previous["close"]) - 1) * 100
    close = float(latest["close"])
    sma = float(latest["sma"])

    buy_checks = {
        "above_sma": close > sma,
        "high_breakout": close > prior_high,
        "return": day_return_pct >= min_return_pct,
    }
    sell_checks = {
        "below_sma": close < sma,
        "low_breakout": close < prior_low,
        "return": day_return_pct <= -min_return_pct,
    }

    buy_missing = [name for name, ok in buy_checks.items() if not ok]
    sell_missing = [name for name, ok in sell_checks.items() if not ok]

    return (
        f"close={close:.2f} sma={sma:.2f} return={day_return_pct:.2f}% "
        f"buy_missing={','.join(buy_missing) or 'none'} "
        f"sell_missing={','.join(sell_missing) or 'none'}"
    )
