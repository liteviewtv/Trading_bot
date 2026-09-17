"""Paper-position protection and monitoring."""

from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.requests import MarketOrderRequest


def monitor_positions(client, stop_loss_pct: float = 0.02, take_profit_pct: float = 0.04):
    """Close paper positions when configured stop/target levels are reached.

    The current implementation uses the broker's latest position mark as a
    conservative monitoring signal. It does not enable live trading.
    """
    positions = client.get_all_positions()
    actions = []

    for position in positions:
        qty = abs(float(position.qty))
        if qty == 0:
            continue
        entry = float(position.avg_entry_price)
        current = float(position.current_price)
        side = str(position.side).lower()

        if side == "long":
            stop = entry * (1 - stop_loss_pct)
            target = entry * (1 + take_profit_pct)
            hit = current <= stop or current >= target
            exit_side = OrderSide.SELL
        else:
            stop = entry * (1 + stop_loss_pct)
            target = entry * (1 - take_profit_pct)
            hit = current >= stop or current <= target
            exit_side = OrderSide.BUY

        if hit:
            order = MarketOrderRequest(
                symbol=position.symbol,
                qty=qty,
                side=exit_side,
                time_in_force=TimeInForce.DAY,
            )
            submitted = client.submit_order(order_data=order)
            actions.append({"symbol": position.symbol, "reason": "stop_or_target", "order_id": str(submitted.id)})

    return actions
