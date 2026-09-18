"""Deterministic trend/momentum breakout signal engine.

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


def _indicators(bars, fast_period, slow_period, breakout_lookback):
    data = bars.copy()
    data["ema_fast"] = data["close"].ewm(span=fast_period, adjust=False).mean()
    data["ema_slow"] = data["close"].ewm(span=slow_period, adjust=False).mean()
    delta = data["close"].diff()
    gain = delta.clip(lower=0).rolling(14).mean()
    loss = (-delta.clip(upper=0)).rolling(14).mean()
    rs = gain / loss.replace(0, pd.NA)
    data["rsi"] = (100 - (100 / (1 + rs))).fillna(50)
    prior = data.iloc[-breakout_lookback-1:-1]
    return data, prior


def generate_signal(symbol: str, bars: pd.DataFrame, sma_period: int = 50,
                    breakout_lookback: int = 20, min_return_pct: float = 0.05,
                    breakout_margin_pct: float = 0.05, min_volume_ratio: float = 0.5):
    """Generate a trend-confirmed momentum breakout signal.

    The legacy arguments are retained for compatibility. The strategy now uses
    EMA50/EMA200 trend alignment, a 20-bar breakout, RSI confirmation and a
    small one-bar momentum threshold. Volume confirms the setup when reliable
    volume is available, but zero/missing volume does not silently block every
    crypto signal.
    """
    fast_period = sma_period
    slow_period = max(200, fast_period * 4)
    required = max(slow_period, breakout_lookback + 1, 22) + 1
    if len(bars) < required:
        return None
    if min_return_pct < 0 or breakout_margin_pct < 0 or min_volume_ratio < 0:
        raise ValueError("strategy thresholds must be non-negative")

    data, prior = _indicators(bars, fast_period, slow_period, breakout_lookback)
    latest, previous = data.iloc[-1], data.iloc[-2]
    close = float(latest["close"])
    prev_close = float(previous["close"])
    ema_fast = float(latest["ema_fast"])
    ema_slow = float(latest["ema_slow"])
    rsi = float(latest["rsi"])
    prior_high = float(prior["high"].max())
    prior_low = float(prior["low"].min())
    ret = (close / prev_close - 1) * 100 if prev_close else 0.0

    high_breakout = close > prior_high * (1 + breakout_margin_pct / 100)
    low_breakout = close < prior_low * (1 - breakout_margin_pct / 100)

    volume_ratio = None
    if "v" in data.columns:
        volume = float(latest["v"])
        avg_volume = float(data["v"].iloc[-21:-1].mean())
        if avg_volume > 0 and volume > 0:
            volume_ratio = volume / avg_volume
    volume_buy_ok = volume_ratio is None or volume_ratio >= min_volume_ratio
    volume_sell_ok = volume_ratio is None or volume_ratio >= min_volume_ratio

    buy = (
        close > ema_fast > ema_slow
        and high_breakout
        and ret >= min_return_pct
        and 52 <= rsi <= 75
        and volume_buy_ok
    )
    sell = (
        close < ema_fast < ema_slow
        and low_breakout
        and ret <= -min_return_pct
        and 25 <= rsi <= 48
        and volume_sell_ok
    )

    if buy:
        volume_text = "volume unavailable" if volume_ratio is None else f"volume ratio {volume_ratio:.2f}"
        return Signal(symbol, "BUY", close,
                      f"EMA{fast_period}>EMA{slow_period}, {breakout_lookback}-bar high breakout, "
                      f"return {ret:.2f}%, RSI {rsi:.1f}, {volume_text}")
    if sell:
        volume_text = "volume unavailable" if volume_ratio is None else f"volume ratio {volume_ratio:.2f}"
        return Signal(symbol, "SELL", close,
                      f"EMA{fast_period}<EMA{slow_period}, {breakout_lookback}-bar low breakout, "
                      f"return {ret:.2f}%, RSI {rsi:.1f}, {volume_text}")
    return None


def diagnose_signal(symbol: str, bars: pd.DataFrame, sma_period: int = 50,
                    breakout_lookback: int = 20, min_return_pct: float = 0.05,
                    breakout_margin_pct: float = 0.05, min_volume_ratio: float = 0.5) -> str:
    """Explain why the latest bar did not generate a signal."""
    fast_period = sma_period
    slow_period = max(200, fast_period * 4)
    required = max(slow_period, breakout_lookback + 1, 22) + 1
    if len(bars) < required:
        return f"insufficient bars ({len(bars)}/{required})"

    data, prior = _indicators(bars, fast_period, slow_period, breakout_lookback)
    latest, previous = data.iloc[-1], data.iloc[-2]
    close = float(latest["close"])
    prev_close = float(previous["close"])
    ema_fast = float(latest["ema_fast"])
    ema_slow = float(latest["ema_slow"])
    rsi = float(latest["rsi"])
    prior_high = float(prior["high"].max())
    prior_low = float(prior["low"].min())
    ret = (close / prev_close - 1) * 100 if prev_close else 0.0
    high_breakout = close > prior_high * (1 + breakout_margin_pct / 100)
    low_breakout = close < prior_low * (1 - breakout_margin_pct / 100)

    volume_ratio = None
    if "v" in data.columns:
        volume = float(latest["v"])
        avg_volume = float(data["v"].iloc[-21:-1].mean())
        if avg_volume > 0 and volume > 0:
            volume_ratio = volume / avg_volume
    volume_ok = volume_ratio is None or volume_ratio >= min_volume_ratio

    buy_missing = []
    if not (close > ema_fast > ema_slow): buy_missing.append("trend")
    if not high_breakout: buy_missing.append("high_breakout")
    if ret < min_return_pct: buy_missing.append("return")
    if not (52 <= rsi <= 75): buy_missing.append("rsi")
    if not volume_ok: buy_missing.append("volume")
    sell_missing = []
    if not (close < ema_fast < ema_slow): sell_missing.append("trend")
    if not low_breakout: sell_missing.append("low_breakout")
    if ret > -min_return_pct: sell_missing.append("return")
    if not (25 <= rsi <= 48): sell_missing.append("rsi")
    if not volume_ok: sell_missing.append("volume")

    return (f"close={close:.6g} ema{fast_period}={ema_fast:.6g} ema{slow_period}={ema_slow:.6g} "
            f"rsi={rsi:.1f} return={ret:.2f}% "
            f"buy_missing={','.join(buy_missing) or 'none'} "
            f"sell_missing={','.join(sell_missing) or 'none'}")
