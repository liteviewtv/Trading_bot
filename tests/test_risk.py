from src.risk import position_size


def test_position_size_respects_risk_and_value_caps():
    # $100 risk budget permits 50 shares, but the 10% position-value cap
    # limits a $10,000 account to $1,000 / $100 = 10 shares.
    assert position_size(10_000, 100, 98) == 10


def test_invalid_stop_returns_zero():
    assert position_size(10_000, 100, 100) == 0
