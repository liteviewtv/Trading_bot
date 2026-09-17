"""Paper-trading performance tracking; never submits broker orders."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PaperTrade:
    symbol: str
    action: str
    entry: float
    exit: float
    confidence: float = 0.0

    @property
    def pnl_pct(self) -> float:
        direction = 1 if self.action.upper() == "BUY" else -1
        return direction * (self.exit - self.entry) / self.entry * 100 if self.entry else 0.0

    @property
    def win(self) -> bool:
        return self.pnl_pct > 0


def summarize_paper_trades(trades: list[PaperTrade]) -> dict:
    returns = [trade.pnl_pct for trade in trades]
    equity = 100.0
    peak = 100.0
    max_drawdown = 0.0
    for result in returns:
        equity *= 1 + result / 100
        peak = max(peak, equity)
        max_drawdown = max(max_drawdown, (peak - equity) / peak * 100)
    return {
        "trades": len(trades),
        "wins": sum(trade.win for trade in trades),
        "losses": sum(not trade.win for trade in trades),
        "total_return_pct": round(equity - 100.0, 6),
        "average_return_pct": round(sum(returns) / len(returns), 6) if returns else 0.0,
        "max_drawdown_pct": round(max_drawdown, 6),
        "average_confidence": round(sum(t.confidence for t in trades) / len(trades), 6) if trades else 0.0,
    }
