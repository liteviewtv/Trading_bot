"""Build a small, JSON-safe market context for AI analysis."""

from __future__ import annotations


def build_market_context(bars, *, lookback: int = 20) -> dict:
    if lookback <= 0:
        raise ValueError("lookback must be positive")
    rows = list(bars)[-lookback:]
    if not rows:
        return {"bars": 0}

    closes = [float(getattr(row, "close", row["close"] if isinstance(row, dict) else row)) for row in rows]
    first, last = closes[0], closes[-1]
    change_pct = ((last - first) / first * 100.0) if first else 0.0
    highs = [float(getattr(row, "high", row["high"] if isinstance(row, dict) else row)) for row in rows]
    lows = [float(getattr(row, "low", row["low"] if isinstance(row, dict) else row)) for row in rows]
    return {
        "bars": len(rows),
        "close": last,
        "change_pct": round(change_pct, 6),
        "high": max(highs),
        "low": min(lows),
    }
