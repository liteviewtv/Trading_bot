"""Simple, deterministic historical backtester for the current signal strategy."""

from dataclasses import dataclass

import pandas as pd

from .strategy import generate_signal


@dataclass(frozen=True)
class BacktestResult:
    initial_cash: float
    final_cash: float
    total_return_pct: float
    trades: int
    wins: int
    losses: int


def run_backtest(symbol: str, bars: pd.DataFrame, initial_cash: float = 10_000.0,
                 stop_pct: float = 0.02, take_profit_pct: float = 0.04) -> BacktestResult:
    """Run a long-only, one-position-at-a-time simulation.

    Entries occur at the next bar's open after a signal. Exits use stop/take-profit
    levels evaluated against each bar's high/low. This is a research simulator,
    not an execution model.
    """
    if initial_cash <= 0 or bars.empty:
        return BacktestResult(initial_cash, initial_cash, 0.0, 0, 0, 0)

    data = bars.sort_index().copy()
    cash = float(initial_cash)
    shares = 0
    entry = 0.0
    stop = 0.0
    target = 0.0
    trades = wins = losses = 0

    for i in range(len(data) - 1):
        row = data.iloc[i]

        if shares:
            low, high = float(row["low"]), float(row["high"])
            exit_price = None
            if low <= stop:
                exit_price = stop
            elif high >= target:
                exit_price = target
            if exit_price is not None:
                cash += shares * exit_price
                trades += 1
                if exit_price > entry:
                    wins += 1
                else:
                    losses += 1
                shares = 0
                continue

        if shares == 0:
            signal = generate_signal(symbol, data.iloc[: i + 1])
            if signal:
                next_open = float(data.iloc[i + 1]["open"])
                qty = int(cash // next_open)
                if qty > 0:
                    shares = qty
                    cash -= qty * next_open
                    entry = next_open
                    stop = entry * (1 - stop_pct)
                    target = entry * (1 + take_profit_pct)

    if shares:
        cash += shares * float(data.iloc[-1]["close"])
        trades += 1
        if float(data.iloc[-1]["close"]) > entry:
            wins += 1
        else:
            losses += 1

    total_return_pct = (cash / initial_cash - 1) * 100
    return BacktestResult(initial_cash, cash, total_return_pct, trades, wins, losses)
