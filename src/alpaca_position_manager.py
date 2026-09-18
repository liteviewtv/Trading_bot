"""Risk checks for Alpaca paper positions."""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from .alpaca_client import positions, open_orders, recent_orders


@dataclass(frozen=True)
class PositionState:
    open_count: int
    symbols: frozenset[str]
    can_open: bool
    reason: str


def _market_symbol(symbol: str) -> str:
    """Normalize Alpaca position/order symbols to the crypto market-data form."""
    value = str(symbol or "").strip().upper()
    if "/" in value:
        return value
    if value.endswith("USD") and len(value) > 3:
        return f"{value[:-3]}/USD"
    return value


def inspect_positions(symbol, max_open_positions=5, *, cooldown_minutes=30,
                      current_positions=None, current_orders=None, historical_orders=None):
    if max_open_positions < 0:
        raise ValueError("max_open_positions must be non-negative")
    if cooldown_minutes < 0:
        raise ValueError("cooldown_minutes must be non-negative")

    requested = _market_symbol(symbol)
    current = list(positions() if current_positions is None else current_positions)
    orders = list(open_orders() if current_orders is None else current_orders)
    history = list(recent_orders() if historical_orders is None else historical_orders)

    symbols = frozenset(_market_symbol(p.get("symbol", "")) for p in current)
    pending = frozenset(
        _market_symbol(o.get("symbol", ""))
        for o in orders
        if str(o.get("status", "")).lower()
        in {"new", "accepted", "pending_new", "partially_filled"}
    )

    if requested in symbols:
        return PositionState(len(current), symbols, False, "Position already exists for symbol")
    if requested in pending:
        return PositionState(len(current), symbols, False, "Open order already exists for symbol")

    if cooldown_minutes > 0:
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=cooldown_minutes)
        for order in history:
            if _market_symbol(order.get("symbol", "")) != requested:
                continue
            if str(order.get("side", "")).lower() != "buy":
                continue
            timestamp = order.get("submitted_at") or order.get("created_at") or order.get("updated_at")
            if not timestamp:
                continue
            try:
                ts = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
                if ts >= cutoff:
                    return PositionState(
                        len(current), symbols, False,
                        f"Recent BUY order exists for symbol (cooldown {cooldown_minutes}m)"
                    )
            except ValueError:
                continue

    if len(current) >= max_open_positions:
        return PositionState(len(current), symbols, False, "Maximum open positions reached")
    return PositionState(len(current), symbols, True, "Position slot available")
