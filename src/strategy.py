"""Long-only crypto signal engine with trend continuation and oversold-reversal entries.

Signals are informational only; this module never submits orders.

The engine deliberately combines two complementary long setups:
1. Trend continuation: EMA50 > EMA200 + positive momentum + RSI confirmation.
2. Oversold reversal: RSI(14) crosses back above 30 after an oversold reading,
   with a structural EMA200 distance guard.

The second route is important for a spot-only Alpaca account: a bearish market
can produce many SELL conditions, but SELL cannot create a new short position.
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

    data["bb_mid"] = data["close"].rolling(20).mean()
    bb_std = data["close"].rolling(20).std()
    data["bb_upper"] = data["bb_mid"] + 2.0 * bb_std
    data["bb_lower"] = data["bb_mid"] - 2.0 * bb_std

    prior = data.iloc[-breakout_lookback - 1:-1]
    return data, prior


def _volume_ratio(data):
    if "v" in data.columns:
        volume = float(data["v"].iloc[-1])
        avg_volume = float(data["v"].iloc[-21:-1].mean())
    elif "volume" in data.columns:
        volume = float(data["volume"].iloc[-1])
        avg_volume = float(data["volume"].iloc[-21:-1].mean())
    else:
        return None

    if avg_volume <= 0 or volume <= 0:
        return None
    return volume / avg_volume


def generate_signal(
    symbol: str,
    bars: pd.DataFrame,
    sma_period: int = 50,
    breakout_lookback: int = 20,
    min_return_pct: float = 0.20,
    breakout_margin_pct: float = 0.05,
    min_volume_ratio: float = 0.5,
):
    """Generate a long-only-friendly trend/reversal signal.

    Trend entries require EMA50 > EMA200, positive 4-bar momentum, RSI in a
    healthy momentum band, and either a breakout or continuation above EMA50.

    Reversal entries wait for RSI(14) to cross back above 30 after being
    oversold, require the current candle to turn positive, and reject assets
    that are more than 8% below EMA200. This avoids buying every falling knife
    while still allowing paper trades during broad bearish conditions.

    SELL remains available as an exit signal for an existing long position.
    Alpaca spot crypto cannot use SELL to open a short position.
    """
    fast_period = sma_period
    slow_period = max(200, fast_period * 4)
    momentum_lookback = 4
    required = max(
        slow_period + 1,
        breakout_lookback + 1,
        22,
        momentum_lookback + 1,
    )

    if len(bars) < required:
        return None
    if min_return_pct < 0 or breakout_margin_pct < 0 or min_volume_ratio < 0:
        raise ValueError("strategy thresholds must be non-negative")

    data, prior = _indicators(bars, fast_period, slow_period, breakout_lookback)
    latest = data.iloc[-1]
    previous = data.iloc[-2]

    close = float(latest["close"])
    prev_close = float(previous["close"])
    ema_fast = float(latest["ema_fast"])
    ema_slow = float(latest["ema_slow"])
    rsi = float(latest["rsi"])
    previous_rsi = float(previous["rsi"])

    prior_high = float(prior["high"].max())
    prior_low = float(prior["low"].min())

    one_bar_return = (close / prev_close - 1) * 100 if prev_close else 0.0
    momentum_start = float(data["close"].iloc[-1 - momentum_lookback])
    momentum_return = (close / momentum_start - 1) * 100 if momentum_start else 0.0

    high_breakout = close > prior_high * (1 + breakout_margin_pct / 100)
    low_breakout = close < prior_low * (1 - breakout_margin_pct / 100)

    volume_ratio = _volume_ratio(data)
    volume_ok = volume_ratio is None or volume_ratio >= min_volume_ratio

    trend_up = close > ema_fast > ema_slow
    trend_down = close < ema_fast < ema_slow

    ema_distance_pct = (close / ema_slow - 1) * 100 if ema_slow else 0.0
    not_severely_below_ema200 = ema_distance_pct >= -8.0
    not_overextended = ((close / ema_fast - 1) * 100 if ema_fast else 0.0) <= 6.0

    buy_momentum = momentum_return >= min_return_pct and one_bar_return > 0
    sell_momentum = momentum_return <= -min_return_pct and one_bar_return < 0

    # Route A: trend continuation / breakout.
    continuation_buy = (
        trend_up
        and 50 <= rsi <= 72
        and buy_momentum
        and (high_breakout or close > ema_fast)
        and not_overextended
        and volume_ok
    )

    # Route B: oversold reversal. We wait for the RSI cross-back instead of
    # buying merely because RSI is low. This is materially safer than entering
    # while RSI is still falling.
    reversal_buy = (
        previous_rsi < 30 <= rsi
        and one_bar_return > 0
        and not_severely_below_ema200
        and close >= float(latest["bb_lower"]) if pd.notna(latest["bb_lower"]) else False
    )

    if continuation_buy:
        volume_text = (
            "volume unavailable"
            if volume_ratio is None
            else f"volume ratio {volume_ratio:.2f}"
        )
        entry_text = "breakout" if high_breakout else "EMA continuation"
        return Signal(
            symbol,
            "BUY",
            close,
            f"EMA{fast_period}>EMA{slow_period}, {entry_text}, "
            f"{momentum_lookback}-bar momentum {momentum_return:.2f}%, "
            f"RSI {rsi:.1f}, {volume_text}",
        )

    if reversal_buy:
        return Signal(
            symbol,
            "BUY",
            close,
            f"RSI oversold reversal: RSI crossed {previous_rsi:.1f}->"
            f"{rsi:.1f}, 1-bar return {one_bar_return:.2f}%, "
            f"EMA{slow_period} distance {ema_distance_pct:.2f}%",
        )

    # SELL is an exit-only signal for the Alpaca spot account.
    sell = (
        trend_down
        and 28 <= rsi <= 50
        and sell_momentum
        and (low_breakout or close < ema_fast)
        and volume_ok
    )

    if sell:
        volume_text = (
            "volume unavailable"
            if volume_ratio is None
            else f"volume ratio {volume_ratio:.2f}"
        )
        entry_text = "breakdown" if low_breakout else "EMA continuation"
        return Signal(
            symbol,
            "SELL",
            close,
            f"EMA{fast_period}<EMA{slow_period}, {entry_text}, "
            f"{momentum_lookback}-bar momentum {momentum_return:.2f}%, "
            f"RSI {rsi:.1f}, {volume_text}",
        )

    return None


def diagnose_signal(
    symbol: str,
    bars: pd.DataFrame,
    sma_period: int = 50,
    breakout_lookback: int = 20,
    min_return_pct: float = 0.20,
    breakout_margin_pct: float = 0.05,
    min_volume_ratio: float = 0.5,
) -> str:
    """Explain why the latest bar did not generate a signal."""
    fast_period = sma_period
    slow_period = max(200, fast_period * 4)
    momentum_lookback = 4
    required = max(
        slow_period + 1,
        breakout_lookback + 1,
        22,
        momentum_lookback + 1,
    )

    if len(bars) < required:
        return f"insufficient bars ({len(bars)}/{required})"

    data, prior = _indicators(bars, fast_period, slow_period, breakout_lookback)
    latest = data.iloc[-1]
    previous = data.iloc[-2]

    close = float(latest["close"])
    prev_close = float(previous["close"])
    ema_fast = float(latest["ema_fast"])
    ema_slow = float(latest["ema_slow"])
    rsi = float(latest["rsi"])
    previous_rsi = float(previous["rsi"])

    prior_high = float(prior["high"].max())
    prior_low = float(prior["low"].min())

    one_bar_return = (close / prev_close - 1) * 100 if prev_close else 0.0
    momentum_start = float(data["close"].iloc[-1 - momentum_lookback])
    momentum_return = (close / momentum_start - 1) * 100 if momentum_start else 0.0

    high_breakout = close > prior_high * (1 + breakout_margin_pct / 100)
    low_breakout = close < prior_low * (1 - breakout_margin_pct / 100)

    volume_ratio = _volume_ratio(data)
    volume_ok = volume_ratio is None or volume_ratio >= min_volume_ratio

    ema_distance_pct = (close / ema_slow - 1) * 100 if ema_slow else 0.0
    bb_lower = latest["bb_lower"]
    bb_ok = pd.notna(bb_lower) and close >= float(bb_lower)

    buy_missing = []
    if not (close > ema_fast > ema_slow):
        buy_missing.append("trend")
    if not high_breakout and not (close > ema_fast):
        buy_missing.append("entry")
    if momentum_return < min_return_pct or one_bar_return <= 0:
        buy_missing.append("momentum")
    if not (50 <= rsi <= 72):
        buy_missing.append("rsi")
    if not volume_ok:
        buy_missing.append("volume")
    if ema_fast and (close / ema_fast - 1) * 100 > 6.0:
        buy_missing.append("extended")

    reversal_missing = []
    if not (previous_rsi < 30 <= rsi):
        reversal_missing.append("rsi_crossback")
    if one_bar_return <= 0:
        reversal_missing.append("bounce")
    if ema_distance_pct < -8.0:
        reversal_missing.append("ema200_distance")
    if not bb_ok:
        reversal_missing.append("below_bb")

    sell_missing = []
    if not (close < ema_fast < ema_slow):
        sell_missing.append("trend")
    if not low_breakout and not (close < ema_fast):
        sell_missing.append("entry")
    if momentum_return > -min_return_pct or one_bar_return >= 0:
        sell_missing.append("momentum")
    if not (28 <= rsi <= 50):
        sell_missing.append("rsi")
    if not volume_ok:
        sell_missing.append("volume")

    volume_text = "unavailable" if volume_ratio is None else f"{volume_ratio:.2f}"
    return (
        f"close={close:.6g} ema{fast_period}={ema_fast:.6g} "
        f"ema{slow_period}={ema_slow:.6g} rsi={rsi:.1f} "
        f"prev_rsi={previous_rsi:.1f} 1bar_return={one_bar_return:.2f}% "
        f"{momentum_lookback}bar_momentum={momentum_return:.2f}% "
        f"high_breakout={str(high_breakout).lower()} "
        f"low_breakout={str(low_breakout).lower()} "
        f"volume_ratio={volume_text} "
        f"buy_missing={','.join(buy_missing) or 'none'} "
        f"reversal_missing={','.join(reversal_missing) or 'none'} "
        f"sell_missing={','.join(sell_missing) or 'none'}"
    )
