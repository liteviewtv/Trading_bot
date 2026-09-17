import pandas as pd

from src.strategy import generate_signal


def test_strategy_returns_none_with_insufficient_data():
    bars = pd.DataFrame({"open": [10], "high": [10], "low": [9], "close": [10], "volume": [1000]})
    assert generate_signal("TEST", bars) is None


def test_strategy_generates_breakout_signal():
    n = 25
    close = [10.0] * 20 + [10.3, 10.4, 10.5, 10.6, 11.0]
    high = [x + 0.05 for x in close]
    low = [x - 0.05 for x in close]
    bars = pd.DataFrame({"open": close, "high": high, "low": low, "close": close, "volume": [1_000_000] * n})
    signal = generate_signal("TEST", bars, sma_period=20, breakout_lookback=10, min_return_pct=2.0)
    assert signal is not None
    assert signal.action == "BUY"


def test_strategy_generates_sell_breakdown_signal():
    n = 25
    close = [10.0] * 20 + [9.7, 9.6, 9.5, 9.4, 9.0]
    high = [x + 0.05 for x in close]
    low = [x - 0.05 for x in close]
    bars = pd.DataFrame({"open": close, "high": high, "low": low, "close": close, "volume": [1_000_000] * n})
    signal = generate_signal("TEST", bars, sma_period=20, breakout_lookback=10, min_return_pct=2.0)
    assert signal is not None
    assert signal.action == "SELL"


def test_strategy_rejects_negative_min_return():
    bars = pd.DataFrame({"open": [10] * 25, "high": [10] * 25, "low": [9] * 25, "close": [10] * 25, "volume": [1000] * 25})
    try:
        generate_signal("TEST", bars, min_return_pct=-1)
        assert False
    except ValueError:
        pass
