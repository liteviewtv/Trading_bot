"""Paper-order execution layer.

Safety invariant: this module refuses to operate unless paper mode is enabled.
"""

from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import MarketOrderRequest

from .config import Settings
from .risk import position_size


def submit_paper_buy(client, settings: Settings, symbol: str, entry_price: float,
                     stop_price: float, equity: float, risk_fraction: float = 0.01,
                     max_position_fraction: float = 0.10):
    """Submit a market BUY to Alpaca's paper account only."""
    if not settings.alpaca_paper:
        raise RuntimeError("Live order submission is disabled.")

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
