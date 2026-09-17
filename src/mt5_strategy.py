"""MT5 strategy adapter with configurable asset-class profiles.

The strategy remains signal-only: it never submits orders.
"""

import json
from pathlib import Path

import pandas as pd

from .strategy import Signal, generate_signal

_CONFIG = Path(__file__).resolve().parent.parent / "config" / "mt5_strategy.json"


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


def asset_class(symbol: str) -> str:
    """Classify common MT5 instruments without requiring broker symbol names."""
    s = symbol.upper().replace("/", "")
    if "XAU" in s or "GOLD" in s:
        return "gold"
    crypto = ("BTC", "ETH", "SOL", "XRP", "DOGE", "LTC", "ADA")
    if any(token in s for token in crypto):
        return "crypto"
    return "forex"


def load_profile(kind: str) -> dict:
    with _CONFIG.open("r", encoding="utf-8") as fh:
        config = json.load(fh)
    return config.get(kind, config["default"])


def generate_mt5_signal(symbol: str, candles, **overrides) -> Signal | None:
    """Generate a signal using an asset-appropriate configurable profile."""
    data = candles_to_dataframe(candles)
    params = load_profile(asset_class(symbol)).copy()
    params.update(overrides)
    return generate_signal(symbol=symbol, bars=data, **params)
