"""Alpaca paper-trading client factory."""

from alpaca.trading.client import TradingClient

from .config import Settings


def create_trading_client(settings: Settings) -> TradingClient:
    """Create an Alpaca client explicitly configured for paper trading."""
    return TradingClient(
        api_key=settings.alpaca_api_key,
        secret_key=settings.alpaca_secret_key,
        paper=True,
    )
