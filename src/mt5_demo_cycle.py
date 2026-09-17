"""Single-symbol MT5 demo trading cycle.

MT5-specific modules are imported lazily so strategy-cycle tests can run on
Linux CI where the MetaTrader 5 terminal/package is unavailable.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class CycleResult:
    symbol: str
    signal: object | None
    submitted: bool
    message: str


def run_demo_cycle(symbol: str, execute: bool = False) -> CycleResult:
    """Evaluate one symbol; execution remains opt-in and demo-only."""
    from .mt5_client import bars, account_info, connect, disconnect, MT5Settings
    from .mt5_execution import calculate_volume, submit_demo_market_order
    from .mt5_strategy import generate_mt5_signal

    settings = MT5Settings.from_env()
    connect(settings)
    try:
        account = account_info()
        if account is None:
            raise RuntimeError("MT5 account information is unavailable")

        raw = bars(symbol)
        frame = pd.DataFrame(raw)
        signal = generate_mt5_signal(symbol, frame)
        if signal is None:
            return CycleResult(symbol, None, False, "No trading signal")
        if not execute:
            return CycleResult(symbol, signal, False, "Signal generated; execution disabled")

        tick_price = float(frame.iloc[-1]["close"])
        risk_fraction = 0.01
        if signal.action == "BUY":
            stop = tick_price * 0.99
            target = tick_price * 1.02
        else:
            stop = tick_price * 1.01
            target = tick_price * 0.98

        volume = calculate_volume(symbol, tick_price, stop, float(account.equity), risk_fraction)
        result = submit_demo_market_order(symbol, signal.action, volume, stop, target)
        return CycleResult(symbol, signal, True, f"Demo order submitted: {getattr(result, 'retcode', result)}")
    finally:
        disconnect()
