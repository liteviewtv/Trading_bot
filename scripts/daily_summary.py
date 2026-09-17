from src.telegram_controls import daily_summary, send_message
from src.trade_store import TradeStore


if __name__ == "__main__":
    send_message(daily_summary(TradeStore()))
