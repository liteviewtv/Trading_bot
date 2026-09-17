"""Phase 1 entry point: verify the Alpaca paper account connection."""

from src.alpaca_client import create_trading_client
from src.config import Settings


def main() -> None:
    settings = Settings.from_env()
    client = create_trading_client(settings)
    account = client.get_account()

    print("Alpaca paper connection: OK")
    print(f"Account status: {account.status}")
    print(f"Equity: {account.equity}")
    print(f"Buying power: {account.buying_power}")


if __name__ == "__main__":
    main()
