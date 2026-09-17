"""Execution backend interfaces for MT5 local terminal or future bridge APIs.

The strategy and risk layers depend on this small interface rather than on a
specific MT5 transport. No network bridge is enabled by default.
"""

from dataclasses import dataclass
from typing import Protocol, Any


@dataclass(frozen=True)
class OrderRequest:
    symbol: str
    side: str
    volume: float
    price: float | None = None
    stop_loss: float | None = None
    take_profit: float | None = None
    comment: str = "Trading_bot"


class ExecutionBackend(Protocol):
    def place_order(self, request: OrderRequest) -> Any: ...
    def close_position(self, symbol: str, ticket: int | None = None) -> Any: ...


class MT5LocalBackend:
    """Adapter for the existing local MT5 terminal execution module."""

    def place_order(self, request: OrderRequest):
        from .mt5_execution import place_market_order
        return place_market_order(
            symbol=request.symbol,
            side=request.side,
            volume=request.volume,
            stop_loss=request.stop_loss,
            take_profit=request.take_profit,
            comment=request.comment,
        )

    def close_position(self, symbol: str, ticket: int | None = None):
        from .mt5_execution import close_position
        return close_position(symbol=symbol, ticket=ticket)


class MT5BridgeBackend:
    """Placeholder for a REST/WebSocket MT5 bridge.

    Deliberately fails closed until a verified bridge endpoint and authentication
    mechanism are configured. This prevents accidental HTTP order submission.
    """

    def __init__(self, base_url: str | None = None, api_key: str | None = None):
        self.base_url = base_url
        self.api_key = api_key

    def _not_configured(self):
        raise RuntimeError("MT5 bridge backend is not configured; no order was sent")

    def place_order(self, request: OrderRequest):
        self._not_configured()

    def close_position(self, symbol: str, ticket: int | None = None):
        self._not_configured()
