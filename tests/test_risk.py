from src.risk import position_size


def test_position_size_respects_risk_and_value_caps():
    assert position_size(10_000, 100, 98) == 50


def test_invalid_stop_returns_zero():
    assert position_size(10_000, 100, 100) == 0
