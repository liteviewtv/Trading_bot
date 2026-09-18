"""Telegram commands backed by live Alpaca paper-account and crypto market data."""
from __future__ import annotations
from .alpaca_client import account, positions as live_positions, recent_orders, crypto_universe, bars

def _num(value, default=0.0):
    try: return float(value)
    except (TypeError, ValueError): return default

def status_message(_summary=None) -> str:
    acct = account()
    pos = live_positions() or []
    orders = recent_orders(limit=20)
    equity = _num(acct.get("equity"))
    cash = _num(acct.get("cash"))
    buying = _num(acct.get("buying_power"))
    day_pl = equity - _num(acct.get("last_equity"))
    return "\n".join(["📊 LIVE ALPACA PAPER STATUS", f"Equity: ${equity:,.2f}", f"Cash: ${cash:,.2f}", f"Buying power: ${buying:,.2f}", f"Day P&L: ${day_pl:,.2f}", f"Open positions: {len(pos)}", f"Recent orders: {len(orders)}"])

def positions_message() -> str:
    pos = live_positions() or []
    if not pos: return "📋 LIVE PAPER POSITIONS\nNo open positions."
    lines = ["📋 LIVE PAPER POSITIONS"]
    for p in pos:
        symbol = p.get("symbol", "?"); qty = p.get("qty", "?")
        entry = _num(p.get("avg_entry_price")); current = _num(p.get("current_price"))
        pnl = _num(p.get("unrealized_plpc")) * 100
        lines.append(f"{symbol} | Qty: {qty} | Entry: ${entry:,.6f} | Now: ${current:,.6f} | P&L: {pnl:+.2f}%")
    return "\n".join(lines)

def orders_message() -> str:
    orders = recent_orders(limit=20)
    if not orders: return "📑 LIVE ORDERS\nNo recent orders."
    lines = ["📑 LIVE ALPACA ORDERS (20 latest)"]
    for o in orders:
        symbol = o.get("symbol", "?"); side = str(o.get("side", "?")).upper(); status = o.get("status", "?")
        qty = o.get("qty") or o.get("notional") or "?"
        lines.append(f"{symbol} {side} | {status} | Qty/Notional: {qty}")
    return "\n".join(lines)

def price_message(command: str) -> str:
    parts = command.strip().split()
    if len(parts) < 2: return "Usage: /price BTC/USD"
    symbol = parts[1].upper()
    if "/" not in symbol and symbol.endswith("USD"): symbol = symbol[:-3] + "/USD"
    data = bars(symbol, timeframe="1Min", limit=2)
    if not data: return f"❌ No live price data for {symbol}."
    price = _num(data[-1].get("c")); previous = _num(data[-2].get("c")) if len(data) > 1 else price
    change = ((price / previous) - 1) * 100 if previous else 0.0
    return f"💹 LIVE PRICE\n{symbol}: ${price:,.8f}\n1-bar change: {change:+.3f}%"

def symbols_message() -> str:
    names = crypto_universe()
    return "📋 LIVE ALPACA CRYPTO SYMBOLS\n" + ("\n".join(names[:100]) if names else "No active tradable USD pairs returned.")

def handle_command(command: str, summary=None, control=None, positions=None) -> str | None:
    raw = command.strip(); cmd = raw.split()[0].lower() if raw else ""
    try:
        if cmd == "/status": return status_message(summary)
        if cmd == "/positions": return positions_message()
        if cmd == "/orders": return orders_message()
        if cmd == "/balance":
            acct = account()
            return f"💰 LIVE PAPER ACCOUNT\nEquity: ${_num(acct.get('equity')):,.2f}\nCash: ${_num(acct.get('cash')):,.2f}\nBuying power: ${_num(acct.get('buying_power')):,.2f}"
        if cmd == "/price": return price_message(raw)
        if cmd == "/symbols": return symbols_message()
        if control is not None and cmd in {"/pause", "/resume"}: return control.handle(cmd, positions)
        if cmd == "/help":
            return ("🤖 LIVE TRADING BOT COMMANDS\n/status — live account + trading status\n/positions — live open positions + P&L\n"
                    "/orders — latest 20 live orders\n/balance — live equity, cash and buying power\n/price SYMBOL — live 1-minute price\n"
                    "/symbols — live tradable crypto pairs\n/pause — stop new paper trades\n/resume — allow new paper trades\n/help — show commands")
    except Exception as exc: return f"❌ LIVE DATA ERROR\n{exc}"
    return None