"""Pure command handling for paper-trading Telegram controls."""
from __future__ import annotations

class DemoControl:
    def __init__(self): self.paused=False
    def handle(self,command,positions=None):
        command=command.strip().split()[0].lower() if command.strip() else ""
        if command.startswith("/pause"): self.paused=True; return "⏸️ Paper trading paused."
        if command.startswith("/resume"): self.paused=False; return "▶️ Paper trading resumed."
        if command.startswith("/positions"):
            positions=positions or []
            if not positions: return "📋 PAPER POSITIONS\nNo open positions."
            lines=["📋 PAPER POSITIONS"]
            for p in positions:
                symbol=getattr(p,"symbol","?"); action=getattr(p,"action","?"); pnl=getattr(p,"pnl_pct",0.0)
                lines.append(f"{symbol} {action} | P&L: {float(pnl):.2f}%")
            return "\n".join(lines)
        if command.startswith("/symbols"):
            try:
                from .alpaca_client import crypto_universe
                names=crypto_universe()
            except Exception as exc: return f"❌ Alpaca crypto symbol discovery failed.\n{exc}"
            if not names: return "📋 ALPACA CRYPTO SYMBOLS\nNo active tradable USD crypto pairs returned."
            shown=names[:100]
            message="📋 ALPACA CRYPTO SYMBOLS\n"+"\n".join(shown)
            if len(names)>len(shown): message += f"\n\n…and {len(names)-len(shown)} more."
            return message
        if command.startswith("/help"):
            return ("🤖 TRADING BOT COMMANDS\n/status — paper performance\n/positions — open paper positions\n"
                    "/symbols — active Alpaca crypto pairs\n/pause — stop new paper trades\n/resume — allow new paper trades\n/help — show commands")
        return None
