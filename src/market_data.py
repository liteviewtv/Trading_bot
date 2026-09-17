"""Market-data helpers for the paper-trading bot."""

from datetime import datetime, timedelta, timezone

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

from .config import Settings


def create_data_client(settings: Settings) -> StockHistoricalDataClient:
    return StockHistoricalDataClient(settings.alpaca_api_key, settings.alpaca_secret_key)


def get_recent_daily_bars(client: StockHistoricalDataClient, symbol: str, days: int = 30):
    """Return recent daily OHLCV bars for a symbol."""
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    request = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=TimeFrame.Day,
        start=start,
        end=end,
    )
    return client.get_stock_bars(request).df
