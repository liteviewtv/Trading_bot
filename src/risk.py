"""Risk calculations. No order submission occurs here."""


def position_size(account_equity: float, entry_price: float, stop_price: float,
                  risk_fraction: float = 0.01, max_position_fraction: float = 0.10) -> int:
    """Calculate whole-share size using fixed fractional risk and a position cap."""
    if account_equity <= 0 or entry_price <= 0 or stop_price <= 0 or entry_price <= stop_price:
        return 0

    risk_per_share = entry_price - stop_price
    risk_budget = account_equity * risk_fraction
    max_position_value = account_equity * max_position_fraction

    by_risk = int(risk_budget // risk_per_share)
    by_value = int(max_position_value // entry_price)
    return max(0, min(by_risk, by_value))
