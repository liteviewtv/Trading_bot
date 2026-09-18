"""MetaTrader 5 connector.

The connector is demo-first: live trading is rejected unless explicitly enabled
in configuration. MT5 Python communicates with a locally installed MT5 terminal.
"""

import os
from dataclasses import dataclass

import MetaTrader5 as mt5


@dataclass(frozen=True)
class MT5Settings:
    login: int
    password: str
    server: str
    terminal_path: str | None
    allow_live: bool = False

    @classmethod
    def from_env(cls) -> "MT5Settings":
        login = os.getenv("MT5_LOGIN", "").strip()
        password = os.getenv("MT5_PASSWORD", "")
        server = os.getenv("MT5_SERVER", "").strip()
        if not login or not password or not server:
            raise RuntimeError("Set MT5_LOGIN, MT5_PASSWORD and MT5_SERVER for the demo account.")
        return cls(int(login), password, server, os.getenv("MT5_TERMINAL_PATH") or None,
                   os.getenv("MT5_ALLOW_LIVE", "false").lower() == "true")


def connect(settings: MT5Settings):
    if settings.allow_live:
        raise RuntimeError("Live MT5 trading is disabled by the initial connector.")
    kwargs = {"login": settings.login, "password": settings.password, "server": settings.server}
    ok = mt5.initialize(settings.terminal_path, **kwargs) if settings.terminal_path else mt5.initialize(**kwargs)
    if not ok:
        error = mt5.last_error()
        mt5.shutdown()
        raise RuntimeError(f"MT5 initialize/login failed: {error}")
    return mt5


def disconnect():
    mt5.shutdown()


def account_info():
    return mt5.account_info()


def positions(symbol: str | None = None):
    values = mt5.positions_get(symbol=symbol) if symbol else mt5.positions_get()
    if values is None:
        raise RuntimeError(f"Could not retrieve MT5 positions: {mt5.last_error()}")
    return values


def symbols(group: str = "*"):
    return mt5.symbols_get(group=group) or ()


def select_symbol(symbol: str):
    info = mt5.symbol_info(symbol)
    if info is None:
        raise ValueError(f"MT5 symbol not found: {symbol}")
    if not info.visible and not mt5.symbol_select(symbol, True):
        raise RuntimeError(f"Could not select MT5 symbol: {symbol}")
    return info


def bars(symbol: str, timeframe=mt5.TIMEFRAME_M15, count: int = 500):
    select_symbol(symbol)
    data = mt5.copy_rates_from_pos(symbol, timeframe, 0, count)
    if data is None:
        raise RuntimeError(f"Could not retrieve bars for {symbol}: {mt5.last_error()}")
    return data


def tick(symbol: str):
    select_symbol(symbol)
    value = mt5.symbol_info_tick(symbol)
    if value is None:
        raise RuntimeError(f"Could not retrieve tick for {symbol}: {mt5.last_error()}")
    return value


def available_instruments():
    """Return the broker's real MT5 instrument names using the configured demo account."""
    settings = MT5Settings.from_env()
    connect(settings)
    try:
        return [s.name for s in symbols()]
    finally:
        disconnect()
