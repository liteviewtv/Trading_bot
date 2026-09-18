"""Execution backend interface and Alpaca paper implementation."""
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

class AlpacaPaperBackend:
    """Primary execution adapter for Alpaca paper trading via REST."""
    def place_order(self, request: OrderRequest):
        from .alpaca_client import submit_market_order
        return submit_market_order(request.symbol, request.side, request.volume)

    def close_position(self, symbol: str, ticket: int | None = None):
        from .alpaca_client import request
        return request("DELETE", f"/v2/positions/{symbol}")

class MT5LocalBackend:
    """Legacy compatibility adapter; not used by the Alpaca runner."""
    def place_order(self, request: OrderRequest):
        from .mt5_execution import place_market_order
        return place_market_order(symbol=request.symbol, side=request.side, volume=request.volume, stop_loss=request.stop_loss, take_profit=request.take_profit, comment=request.comment)

    def close_position(self, symbol: str, ticket: int | None = None):
        from .mt5_execution import close_position
        return close_position(symbol=symbol, ticket=ticket)
