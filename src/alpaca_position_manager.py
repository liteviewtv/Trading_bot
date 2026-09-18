"""Risk checks for Alpaca paper positions."""
from dataclasses import dataclass
from .alpaca_client import positions

@dataclass(frozen=True)
class PositionState:
    open_count: int
    symbols: frozenset[str]
    can_open: bool
    reason: str

def inspect_positions(symbol, max_open_positions=5, *, current_positions=None):
    if max_open_positions < 0: raise ValueError("max_open_positions must be non-negative")
    current = list(positions() if current_positions is None else current_positions)
    symbols = frozenset(str(p.get("symbol", "")) for p in current)
    if symbol in symbols: return PositionState(len(current), symbols, False, "Position already exists for symbol")
    if len(current) >= max_open_positions: return PositionState(len(current), symbols, False, "Maximum open positions reached")
    return PositionState(len(current), symbols, True, "Position slot available")
