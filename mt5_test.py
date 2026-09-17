"""Local MT5 demo connection test.

Run this on a Windows machine with MetaTrader 5 installed and a demo account
configured. Credentials should be supplied through environment variables.
"""

from src.mt5_client import MT5Settings, account_info, available_instruments, connect, disconnect


def main():
    settings = MT5Settings.from_env()
    connect(settings)
    try:
        account = account_info()
        print("MT5 connection: OK")
        print(f"Account: {account.login}")
        print(f"Server: {account.server}")
        print(f"Balance: {account.balance}")
        print(f"Equity: {account.equity}")
        names = available_instruments()
        print(f"Available instruments: {len(names)}")
        for name in ("EURUSD", "XAUUSD", "BTCUSD", "ETHUSD"):
            print(f"{name}: {'available' if name in names else 'not found'}")
    finally:
        disconnect()


if __name__ == "__main__":
    main()
