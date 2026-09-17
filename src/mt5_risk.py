"""MT5-aware risk adapter.

Converts the existing account-level risk policy into broker-aware MT5 volume.
This module calculates and validates size only; it never submits orders.
"""

from dataclasses import dataclass

from .risk import position_size


@dataclass(frozen=True)
class MT5RiskPlan:
    symbol: str
    side: str
    entry_price: float
    stop_price: float
    take_profit: float
    volume: float
    risk_budget: float
    position_value: float


def calculate_mt5_volume(
    account_equity: float,
    entry_price: float,
    stop_price: float,
    contract_size: float,
    volume_min: float,
    volume_max: float,
    volume_step: float,
    risk_fraction: float = 0.01,
    max_position_fraction: float = 0.10,
) -> float:
    """Calculate broker-valid MT5 volume from the existing risk policy."""
    if min(account_equity, entry_price, stop_price, contract_size) <= 0:
        return 0.0
    if entry_price <= stop_price or volume_min <= 0 or volume_max < volume_min or volume_step <= 0:
        return 0.0

    # Existing stock risk engine gives a conservative unit count. Convert its
    # dollar-risk concept to MT5 lots using the broker's contract size.
    risk_per_lot = (entry_price - stop_price) * contract_size
    risk_budget = account_equity * risk_fraction
    max_position_value = account_equity * max_position_fraction
    by_risk = risk_budget / risk_per_lot
    by_value = max_position_value / (entry_price * contract_size)
    raw = min(by_risk, by_value, volume_max)
    stepped = (raw // volume_step) * volume_step
    if stepped < volume_min:
        return 0.0
    return round(stepped, 8)


def build_mt5_risk_plan(
    symbol: str,
    side: str,
    account_equity: float,
    entry_price: float,
    stop_price: float,
    take_profit: float,
    contract_size: float,
    volume_min: float,
    volume_max: float,
    volume_step: float,
    risk_fraction: float = 0.01,
    max_position_fraction: float = 0.10,
) -> MT5RiskPlan:
    """Build a validated MT5 risk plan without placing a trade."""
    if side.upper() not in {"BUY", "SELL"}:
        raise ValueError("side must be BUY or SELL")
    volume = calculate_mt5_volume(
        account_equity, entry_price, stop_price, contract_size,
        volume_min, volume_max, volume_step, risk_fraction, max_position_fraction,
    )
    risk_budget = account_equity * risk_fraction
    position_value = volume * entry_price * contract_size
    return MT5RiskPlan(symbol, side.upper(), entry_price, stop_price, take_profit,
                       volume, risk_budget, position_value)
