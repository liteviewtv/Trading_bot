"""Multi-asset MT5 signal scanner.

Discovers broker-provided symbols instead of assuming exact names for Forex,
gold, and crypto instruments. MT5 is imported lazily through the client so
Linux CI can test symbol resolution without a Windows MT5 terminal.
"""

from __future__ import annotations

from dataclasses import dataclass

from .mt5_strategy import generate_mt5_signal


@dataclass(frozen=True)
class AssetResult:
    requested: str
    symbol: str | None
    signal: object | None
    error: str | None = None


DEFAULT_ASSETS = ("EURUSD", "GBPUSD", "USDJPY", "XAUUSD", "BTCUSD", "ETHUSD")


def resolve_symbol(requested: str, instruments: list[str] | None = None) -> str | None:
    if instruments is None:
        # Import only when a real MT5 scan is requested.
        from .mt5_client import available_instruments
        instruments = available_instruments()
    wanted = requested.upper().replace("/", "")
    exact = next((s for s in instruments if s.upper() == wanted), None)
    if exact:
        return exact
    return next((s for s in instruments if s.upper().startswith(wanted)), None)


def scan_assets(assets=DEFAULT_ASSETS) -> list[AssetResult]:
    from .mt5_client import available_instruments, bars, select_symbol

    instruments = available_instruments()
    results: list[AssetResult] = []
    for requested in assets:
        symbol = resolve_symbol(requested, instruments)
        if symbol is None:
            results.append(AssetResult(requested, None, None, "Symbol unavailable"))
            continue
        try:
            select_symbol(symbol)
            signal = generate_mt5_signal(symbol, bars(symbol))
            results.append(AssetResult(requested, symbol, signal))
        except Exception as exc:
            results.append(AssetResult(requested, symbol, None, str(exc)))
    return results
