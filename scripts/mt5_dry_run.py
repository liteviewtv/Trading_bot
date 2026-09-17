"""End-to-end MT5 demo safety/dry-run.

Connects to the configured MT5 terminal, verifies the account is a demo
account, discovers requested symbols, reads market data, builds a strategy
signal and risk plan, and stops before order_send().
"""

from __future__ import annotations

import os

from src.mt5_client import account_info, initialize, shutdown, select_symbol, tick, bars
from src.mt5_strategy import generate_mt5_signal
from src.mt5_risk import build_mt5_risk_plan


def main() -> int:
    if os.getenv("MT5_ALLOW_LIVE", "false").lower() == "true":
        raise RuntimeError("Dry run refuses to run with MT5_ALLOW_LIVE=true")

    initialize()
    try:
        account = account_info()
        if account is None:
            raise RuntimeError("MT5 account information unavailable")
        trade_mode = getattr(account, "trade_mode", None)
        if trade_mode not in (None, 0):
            # MT5_ACCOUNT_TRADE_MODE_DEMO is 0 in the Python API.
            raise RuntimeError(f"Refusing account with non-demo trade_mode={trade_mode}")

        symbols = [s for s in os.getenv("MT5_SYMBOLS", "EURUSD,XAUUSD,BTCUSD,ETHUSD").split(",") if s]
        print(f"MT5 demo login={getattr(account, 'login', None)} server={getattr(account, 'server', None)}")
        print(f"Balance={getattr(account, 'balance', None)}")

        for symbol in symbols:
            try:
                info = select_symbol(symbol)
                latest = tick(symbol)
                candles = bars(symbol, 15, 200)
                signal = generate_mt5_signal(symbol, candles)
                print(f"{symbol}: tick={latest} candles={len(candles)} signal={signal}")
                if signal is not None:
                    entry = float(latest.ask if signal.side == "BUY" else latest.bid)
                    stop = entry * (1 - 0.02) if signal.side == "BUY" else entry * (1 + 0.02)
                    target = entry * (1 + 0.04) if signal.side == "BUY" else entry * (1 - 0.04)
                    plan = build_mt5_risk_plan(
                        symbol, signal.side, float(account.equity), entry, stop, target,
                        float(info.trade_contract_size), float(info.volume_min),
                        float(info.volume_max), float(info.volume_step),
                    )
                    print(f"  risk_plan={plan}")

        print("DRY RUN COMPLETE: no MT5 order_send() call was made.")
        return 0
    finally:
        shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
