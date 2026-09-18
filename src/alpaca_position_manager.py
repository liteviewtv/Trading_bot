"""Risk checks for Alpaca paper positions."""
from dataclasses import dataclass
from .alpaca_client import positions, open_orders

@dataclass(frozen=True)
class PositionState:
    open_count: int
    symbols: frozenset[str]
    can_open: bool
    reason: str

def inspect_positions(symbol, max_open_positions=5, *, current_positions=None, current_orders=None):
    if max_open_positions < 0: raise ValueError("max_open_positions must be non-negative")
    current = list(positions() if current_positions is None else current_positions)
    orders = list(open_orders() if current_orders is None else current_orders)
    symbols = frozenset(str(p.get("symbol", "")) for p in current)
    pending = frozenset(str(o.get("symbol", "")) for o in orders if str(o.get("status","")).lower() in {"new","accepted","pending_new","partially_filled"} )
    if symbol in symbols: return PositionState(len(current), symbols, False, "Position already exists for symbol")
    if symbol in pending: return PositionState(len(current), symbols, False, "Open order already exists for symbol")
    if len(current) >= max_open_positions: return PositionState(len(current), symbols, False, "Maximum open positions reached")
    return PositionState(len(current), symbols, True, "Position slot available")
