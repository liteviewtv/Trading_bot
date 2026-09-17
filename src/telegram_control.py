"""Pure command handling for demo-mode Telegram controls."""

from __future__ import annotations


class DemoControl:
    def __init__(self):
        self.paused = False

    def handle(self, command: str, positions: list | None = None) -> str | None:
        command = command.strip().split()[0].lower() if command.strip() else ""
        if command.startswith("/pause"):
            self.paused = True
            return "⏸️ Demo trading paused."
        if command.startswith("/resume"):
            self.paused = False
            return "▶️ Demo trading resumed."
        if command.startswith("/positions"):
            positions = positions or []
            if not positions:
                return "📋 DEMO POSITIONS\nNo open positions."
            lines = ["📋 DEMO POSITIONS"]
            for position in positions:
                symbol = getattr(position, "symbol", "?")
                action = getattr(position, "action", "?")
                pnl = getattr(position, "pnl_pct", 0.0)
                lines.append(f"{symbol} {action} | P&L: {float(pnl):.2f}%")
            return "\n".join(lines)
        return None
