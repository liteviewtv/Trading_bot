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
        if command.startswith("/symbols"):
            try:
                from .mt5_client import available_instruments
                instruments = available_instruments()
            except Exception as exc:
                return f"❌ MT5 symbol discovery failed.\n{exc}"
            if not instruments:
                return "📋 MT5 SYMBOLS\nNo instruments returned by the broker."
            # Keep the Telegram response compact while showing the broker's real names.
            shown = instruments[:100]
            message = "📋 MT5 SYMBOLS\n" + "\n".join(shown)
            if len(instruments) > len(shown):
                message += f"\n\n…and {len(instruments) - len(shown)} more."
            return message
        if command.startswith("/help"):
            return (
                "🤖 TRADING BOT COMMANDS\n"
                "/status — paper performance\n"
                "/positions — open demo positions\n"
                "/symbols — broker MT5 symbols\n"
                "/pause — stop new demo trades\n"
                "/resume — allow new demo trades\n"
                "/help — show commands"
            )
        return None
