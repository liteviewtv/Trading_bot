"""MT5 connectivity and symbol health checks. Demo mode only."""

from .mt5_client import MT5Client


def check_mt5(client: MT5Client, symbols: list[str]) -> dict:
    account = client.account_info()
    available = []
    missing = []
    for symbol in symbols:
        if client.symbol_info(symbol):
            available.append(symbol)
        else:
            missing.append(symbol)
    return {
        "connected": account is not None,
        "login": getattr(account, "login", None),
        "server": getattr(account, "server", None),
        "balance": getattr(account, "balance", None),
        "available_symbols": available,
        "missing_symbols": missing,
    }
