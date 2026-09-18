import pandas as pd


from src.strategy import generate_signal


def _bullish_breakout_bars():
    # 200-bar rising base keeps EMA50 above EMA200 while the final 20 bars
    # oscillate upward enough to keep RSI below 72 and finish with a breakout.
    close = [10.0 + 0.01 * i for i in range(200)]
    close += [
        12.0, 11.9, 12.1, 12.0, 12.2,
        12.1, 12.3, 12.2, 12.4, 12.3,
        12.5, 12.4, 12.6, 12.5, 12.7,
        12.6, 12.8, 12.7, 12.9, 13.0,
    ]
    return pd.DataFrame(
        {
            "open": close,
            "high": [price + 0.03 for price in close],
            "low": [price - 0.03 for price in close],
            "close": close,
            "volume": [1_000_000] * len(close),
        }
    )


def test_strategy_returns_none_with_insufficient_data():
    bars = pd.DataFrame(
        {"open": [10], "high": [10], "low": [9], "close": [10], "volume": [1000]}
    )
    assert generate_signal("TEST", bars) is None


def test_strategy_generates_breakout_signal():
    signal = generate_signal(
        "TEST",
        _bullish_breakout_bars(),
        sma_period=50,
        breakout_lookback=10,
        min_return_pct=0.20,
    )
    assert signal is not None
    assert signal.action == "BUY"
    assert "breakout" in signal.reason


def test_strategy_generates_oversold_reversal_signal():
    close = [10.0] * 207
    close += list(__import__("numpy").linspace(10.0, 9.8, 10))
    close += [9.8 * 0.99, 9.8 * 0.985, 9.8 * 1.02]
    bars = pd.DataFrame(
        {
            "open": close,
            "high": [price + 0.01 for price in close],
            "low": [price - 0.01 for price in close],
            "close": close,
            "volume": [1_000_000] * len(close),
        }
    )
    signal = generate_signal("TEST", bars, sma_period=50, breakout_lookback=10)
    assert signal is not None
    assert signal.action == "BUY"
    assert "RSI oversold reversal" in signal.reason


def test_strategy_rejects_negative_min_return():
    bars = pd.DataFrame(
        {
            "open": [10] * 220,
            "high": [10] * 220,
            "low": [9] * 220,
            "close": [10] * 220,
            "volume": [1000] * 220,
        }
    )
    try:
        generate_signal("TEST", bars, min_return_pct=-1)
        assert False
    except ValueError:
        pass
