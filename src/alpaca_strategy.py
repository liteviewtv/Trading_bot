"""Alpaca market-data adapter for the existing strategy engine."""
from __future__ import annotations
import pandas as pd
from .strategy import generate_signal

def candles_to_dataframe(bars):
    data = pd.DataFrame(bars)
    if data.empty: return data
    required = {"o", "h", "l", "c"}
    missing = required - set(data.columns)
    if missing: raise ValueError(f"Alpaca bar data missing columns: {sorted(missing)}")
    return data.rename(columns={"o":"open","h":"high","l":"low","c":"close"})

def generate_alpaca_signal(symbol, bars, *, sma_period=50, breakout_lookback=20, min_return_pct=0.1, breakout_margin_pct=0.15, min_volume_ratio=0.8):
    return generate_signal(symbol=symbol, bars=candles_to_dataframe(bars), sma_period=sma_period, breakout_lookback=breakout_lookback, min_return_pct=min_return_pct, breakout_margin_pct=breakout_margin_pct, min_volume_ratio=min_volume_ratio)
