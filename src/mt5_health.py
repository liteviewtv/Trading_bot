"""MT5 connectivity and symbol health checks. Demo mode only."""

from .mt5_client import account_info, select_symbol


def check_mt5(symbols: list[str]) -> dict:
    """Return connection/account health and broker symbol availability."""
    account = account_info()
    available = []
    missing = []
    for symbol in symbols:
        try:
            select_symbol(symbol)
            available.append(symbol)
        except (ValueError, RuntimeError):
            missing.append(symbol)

    return {
        "connected": account is not None,
        "login": getattr(account, "login", None),
        "server": getattr(account, "server", None),
        "balance": getattr(account, "balance", None),
        "available_symbols": available,
        "missing_symbols": missing,
    }
