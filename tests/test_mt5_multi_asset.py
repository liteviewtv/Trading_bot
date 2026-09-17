from src.mt5_multi_asset import resolve_symbol


def test_resolves_exact_symbol():
    assert resolve_symbol("EURUSD", ["EURUSD", "XAUUSD"]) == "EURUSD"


def test_resolves_broker_suffix():
    assert resolve_symbol("XAUUSD", ["EURUSD", "XAUUSDm", "BTCUSD"]) == "XAUUSDm"


def test_returns_none_when_unavailable():
    assert resolve_symbol("ETHUSD", ["EURUSD", "XAUUSDm"]) is None
