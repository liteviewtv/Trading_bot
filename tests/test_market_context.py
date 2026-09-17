from types import SimpleNamespace

from src.market_context import build_market_context


def test_build_market_context():
    bars = [SimpleNamespace(close=10, high=11, low=9), SimpleNamespace(close=12, high=13, low=10)]
    result = build_market_context(bars)
    assert result == {"bars": 2, "close": 12.0, "change_pct": 20.0, "high": 13.0, "low": 9.0}


def test_empty_market_context():
    assert build_market_context([]) == {"bars": 0}
