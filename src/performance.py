"""Backtest performance metrics."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Performance:
    trades: int
    wins: int
    losses: int
    win_rate_pct: float
    net_pnl: float
    average_trade: float
    profit_factor: float
    max_drawdown_pct: float


def calculate_performance(pnls: list[float], initial_cash: float) -> Performance:
    if not pnls or initial_cash <= 0:
        return Performance(0, 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0)

    wins = sum(p > 0 for p in pnls)
    losses = sum(p <= 0 for p in pnls)
    net = sum(pnls)
    gross_profit = sum(p for p in pnls if p > 0)
    gross_loss = abs(sum(p for p in pnls if p < 0))

    equity = float(initial_cash)
    peak = equity
    max_dd = 0.0
    for pnl in pnls:
        equity += pnl
        peak = max(peak, equity)
        if peak:
            max_dd = max(max_dd, (peak - equity) / peak * 100)

    return Performance(
        trades=len(pnls),
        wins=wins,
        losses=losses,
        win_rate_pct=wins / len(pnls) * 100,
        net_pnl=net,
        average_trade=net / len(pnls),
        profit_factor=(gross_profit / gross_loss) if gross_loss else float("inf"),
        max_drawdown_pct=max_dd,
    )
