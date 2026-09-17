"""Paper-order execution layer with portfolio safety gates."""

from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import MarketOrderRequest

from .config import Settings
from .risk import position_size


def submit_paper_buy(client, settings: Settings, symbol: str, entry_price: float,
                     stop_price: float, equity: float, open_positions: int = 0,
                     trades_this_cycle: int = 0, max_concurrent_positions: int = 5,
                     max_trades_per_cycle: int = 1, risk_fraction: float = 0.01,
                     max_position_fraction: float = 0.10):
    """Submit a market BUY only when all portfolio safety gates pass."""
    if not settings.alpaca_paper:
        raise RuntimeError("Live order submission is disabled.")
    if open_positions >= max_concurrent_positions:
        return None
    if trades_this_cycle >= max_trades_per_cycle:
        return None

    qty = position_size(equity, entry_price, stop_price, risk_fraction, max_position_fraction)
    if qty < 1:
        return None

    order = MarketOrderRequest(
        symbol=symbol,
        qty=qty,
        side=OrderSide.BUY,
        time_in_force=TimeInForce.DAY,
    )
    return client.submit_order(order_data=order)
