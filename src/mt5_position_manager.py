"""Safety checks for existing MT5 demo positions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PositionState:
    open_count: int
    symbols: frozenset[str]
    can_open: bool
    reason: str


def inspect_positions(symbol: str, max_open_positions: int = 5, *, account=None, current_positions=None) -> PositionState:
    """Return whether a new position can be opened."""
    if max_open_positions < 0:
        raise ValueError("max_open_positions must be non-negative")
    if account is None or current_positions is None:
        from .mt5_client import account_info, positions
        account = account_info()
        current_positions = positions()
    if account is None:
        raise RuntimeError("MT5 account information is unavailable")
    current = list(current_positions)
    symbols = frozenset(getattr(p, "symbol", "") for p in current)
    if symbol in symbols:
        return PositionState(len(current), symbols, False, "Position already exists for symbol")
    if len(current) >= max_open_positions:
        return PositionState(len(current), symbols, False, "Maximum open positions reached")
    return PositionState(len(current), symbols, True, "Position slot available")
