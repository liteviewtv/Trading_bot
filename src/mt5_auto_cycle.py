"""Multi-asset automatic MT5 demo cycle with AI filtering and journaling."""

from __future__ import annotations

from dataclasses import dataclass

from .ai_filter import AIFilterDecision, filter_signal
from .mt5_demo_cycle import run_demo_cycle
from .mt5_multi_asset import AssetResult, DEFAULT_ASSETS, scan_assets
from .mt5_position_manager import inspect_positions
from .trade_journal import append_entry, make_entry
from .telegram_notify import TelegramNotifier


@dataclass(frozen=True)
class AutoCycleResult:
    scanned: list[AssetResult]
    executed: list[object]
    skipped: list[str]


def run_auto_demo_cycle(
    assets=DEFAULT_ASSETS,
    execute: bool = False,
    max_orders: int = 2,
    max_open_positions: int = 5,
    journal_path=None,
    ai_decisions: dict[str, AIFilterDecision] | None = None,
    ai_min_confidence: float = 0.60,
    ai_analyzer=None,
    notifier: TelegramNotifier | None = None,
    control=None,
) -> AutoCycleResult:
    """Scan assets and submit only signals passing AI and risk gates."""
    if max_orders < 0 or max_open_positions < 0:
        raise ValueError("position/order limits must be non-negative")
    if not 0.0 <= ai_min_confidence <= 1.0:
        raise ValueError("ai_min_confidence must be between 0 and 1")

    notifier = notifier or TelegramNotifier()
    scanned = scan_assets(assets)
    executed: list[object] = []
    skipped: list[str] = []

    def journal(symbol, event, reason=None, signal=None, result=None):
        if journal_path is not None:
            append_entry(journal_path, make_entry(event, symbol, reason=reason,
                action=getattr(signal, "action", None), result=result))

    def notify(event, details=""):
        try:
            notifier.event(event, details)
        except Exception:
            pass

    if execute and control is not None and getattr(control, "paused", False):
        skipped.append("demo trading paused")
        notify("⏸️ DEMO TRADING PAUSED", "No new paper trades were opened.")
        return AutoCycleResult(scanned, executed, skipped)

    for item in scanned:
        symbol = item.symbol or item.requested
        if item.signal is None:
            reason = item.error or "No trading signal"
            skipped.append(f"{item.requested}: no signal")
            journal(symbol, "skipped", reason=reason)
            notify("⚠️ SIGNAL SKIPPED", f"Symbol: {symbol}\nReason: {reason}")
            continue
        if not execute:
            skipped.append(f"{item.requested}: execution disabled")
            journal(symbol, "signal", reason="execution disabled", signal=item.signal)
            notify("🤖 AI/STRATEGY SIGNAL", f"Symbol: {symbol}\nAction: {getattr(item.signal, 'action', 'UNKNOWN')}\nMode: paper/demo")
            continue
        if len(executed) >= max_orders:
            skipped.append(f"{item.requested}: order limit reached")
            journal(symbol, "skipped", reason="order limit reached", signal=item.signal)
            notify("⚠️ ORDER SKIPPED", f"Symbol: {symbol}\nReason: order limit reached")
            continue

        if ai_analyzer is not None:
            try:
                analysis = ai_analyzer.analyze(item.signal, {"symbol": symbol})
                ai_decisions = dict(ai_decisions or {})
                ai_decisions[symbol] = AIFilterDecision(
                    str(analysis.decision).upper(), float(analysis.confidence), str(analysis.reason)
                )
                notify("🤖 AI DECISION", f"Symbol: {symbol}\nDecision: {analysis.decision}\nConfidence: {float(analysis.confidence):.0%}\nReason: {analysis.reason}")
            except Exception as exc:
                skipped.append(f"{item.requested}: AI analysis failed")
                journal(symbol, "skipped", reason=f"AI analysis failed: {exc}", signal=item.signal)
                notify("❌ AI ANALYSIS FAILED", f"Symbol: {symbol}\nError: {exc}")
                continue

        if ai_decisions is not None:
            ai_decision = ai_decisions.get(symbol) or ai_decisions.get(item.requested)
            if ai_decision is None:
                skipped.append(f"{item.requested}: AI decision unavailable")
                journal(symbol, "skipped", reason="AI decision unavailable", signal=item.signal)
                notify("⚠️ AI DECISION MISSING", f"Symbol: {symbol}")
                continue
            filtered = filter_signal(item.signal, ai_decision, ai_min_confidence)
            if filtered.action == "HOLD":
                skipped.append(f"{item.requested}: {filtered.reason}")
                journal(symbol, "skipped", reason=filtered.reason, signal=item.signal)
                notify("⏸️ TRADE REJECTED", f"Symbol: {symbol}\nReason: {filtered.reason}")
                continue

        state = inspect_positions(symbol, max_open_positions=max_open_positions)
        if not state.can_open:
            skipped.append(f"{item.requested}: {state.reason}")
            journal(symbol, "skipped", reason=state.reason, signal=item.signal)
            notify("🛡️ TRADE BLOCKED", f"Symbol: {symbol}\nReason: {state.reason}")
            continue

        result = run_demo_cycle(symbol, execute=True)
        executed.append(result)
        journal(symbol, "executed", signal=item.signal, result=str(getattr(result, "message", result)))
        notify("✅ PAPER TRADE", f"Symbol: {symbol}\nAction: {getattr(item.signal, 'action', 'UNKNOWN')}\nResult: {getattr(result, 'message', result)}")

    return AutoCycleResult(scanned, executed, skipped)
