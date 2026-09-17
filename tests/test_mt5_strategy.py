import pandas as pd

from src.mt5_strategy import asset_class, candles_to_dataframe, generate_mt5_signal


def make_bars(values):
    return pd.DataFrame({
        "open": values,
        "high": [v + 0.05 for v in values],
        "low": [v - 0.05 for v in values],
        "close": values,
        "volume": [1000] * len(values),
    })


def test_asset_classes():
    assert asset_class("EURUSD") == "forex"
    assert asset_class("XAUUSD") == "gold"
    assert asset_class("BTCUSD") == "crypto"
    assert asset_class("GOLDm") == "gold"


def test_candle_normalization():
    data = candles_to_dataframe(make_bars([10.0] * 55))
    assert list(data["close"]) == [10.0] * 55


def test_missing_candle_column_is_rejected():
    try:
        candles_to_dataframe(pd.DataFrame({"open": [1], "high": [1], "low": [1]}))
        assert False
    except ValueError as exc:
        assert "close" in str(exc)


def test_mt5_strategy_can_generate_sell_signal():
    # The EURUSD profile requires 50 SMA bars plus a breakout bar.
    values = [10.0] * 50 + [9.7, 9.6, 9.5, 9.4, 9.0]
    signal = generate_mt5_signal("EURUSD", make_bars(values))
    assert signal is not None
    assert signal.action == "SELL"
