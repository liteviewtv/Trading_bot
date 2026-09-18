"""Alpaca-backed automatic paper-trading cycle."""
from dataclasses import dataclass
from uuid import uuid4
from .ai_filter import AIFilterDecision, filter_signal
from .alpaca_client import bars, submit_market_order, tradable_asset
from .alpaca_position_manager import inspect_positions
from .alpaca_strategy import generate_alpaca_signal
from .trade_journal import append_entry, make_entry
from .telegram_notify import TelegramNotifier

@dataclass(frozen=True)
class AssetResult:
    requested: str
    symbol: str | None
    signal: object | None
    error: str | None = None

@dataclass(frozen=True)
class AutoCycleResult:
    scanned: list[AssetResult]
    executed: list[object]
    skipped: list[str]

def scan_assets(assets):
    results=[]
    for symbol in assets:
        try:
            asset=tradable_asset(symbol)
            if not asset or not asset.get("tradable"):
                results.append(AssetResult(symbol,None,None,"Asset unavailable or not tradable")); continue
            results.append(AssetResult(symbol,symbol,generate_alpaca_signal(symbol,bars(symbol))))
        except Exception as exc:
            results.append(AssetResult(symbol,symbol,None,str(exc)))
    return results

def run_auto_demo_cycle(assets, execute=False, max_orders=2, max_open_positions=5, journal_path=None, ai_decisions=None, ai_min_confidence=0.60, ai_analyzer=None, notifier=None, control=None):
    if max_orders < 0 or max_open_positions < 0: raise ValueError("position/order limits must be non-negative")
    notifier=notifier or TelegramNotifier(); scanned=scan_assets(assets); executed=[]; skipped=[]
    def journal(symbol,event,reason=None,signal=None,result=None):
        if journal_path is not None: append_entry(journal_path,make_entry(event,symbol,reason=reason,action=getattr(signal,"action",None),result=result))
    def notify(event,details=""):
        try: notifier.event(event,details)
        except Exception: pass
    if execute and control is not None and getattr(control,"paused",False): return AutoCycleResult(scanned,executed,["paper trading paused"])
    for item in scanned:
        symbol=item.symbol or item.requested
        if item.signal is None:
            reason=item.error or "No trading signal"
            skipped.append(f"{item.requested}: no signal")
            journal(symbol,"skipped",reason=reason)
            # A normal no-signal result is expected and is deliberately silent.
            # Telegram is reserved for actionable signals, errors, blocks and orders.
            if reason not in {"Asset unavailable or not tradable", "No trading signal"}:
                notify("⚠️ SIGNAL SKIPPED",f"Symbol: {symbol}\nReason: {reason}")
            continue
        if not execute:
            skipped.append(f"{item.requested}: execution disabled"); journal(symbol,"signal",reason="execution disabled",signal=item.signal); notify("🤖 PAPER SIGNAL",f"Symbol: {symbol}\nAction: {item.signal.action}\nMode: Alpaca paper"); continue
        if len(executed) >= max_orders:
            skipped.append(f"{item.requested}: order limit reached"); journal(symbol,"skipped",reason="order limit reached",signal=item.signal); notify("⚠️ ORDER SKIPPED",f"Symbol: {symbol}\nReason: order limit reached"); continue
        if ai_analyzer is not None:
            try:
                analysis=ai_analyzer.analyze(item.signal,{"symbol":symbol}); ai_decisions=dict(ai_decisions or {}); ai_decisions[symbol]=AIFilterDecision(str(analysis.decision).upper(),float(analysis.confidence),str(analysis.reason))
            except Exception as exc:
                skipped.append(f"{item.requested}: AI analysis failed"); journal(symbol,"skipped",reason=f"AI analysis failed: {exc}",signal=item.signal); notify("❌ AI ANALYSIS FAILED",f"Symbol: {symbol}\nError: {exc}"); continue
        if ai_decisions is not None:
            decision=ai_decisions.get(symbol) or ai_decisions.get(item.requested)
            if decision is None: skipped.append(f"{item.requested}: AI decision unavailable"); journal(symbol,"skipped",reason="AI decision unavailable",signal=item.signal); continue
            filtered=filter_signal(item.signal,decision,ai_min_confidence)
            if filtered.action == "HOLD": skipped.append(f"{item.requested}: {filtered.reason}"); journal(symbol,"skipped",reason=filtered.reason,signal=item.signal); notify("⏸️ TRADE REJECTED",f"Symbol: {symbol}\nReason: {filtered.reason}"); continue
        state=inspect_positions(symbol,max_open_positions=max_open_positions)
        if not state.can_open:
            skipped.append(f"{item.requested}: {state.reason}"); journal(symbol,"skipped",reason=state.reason,signal=item.signal); notify("🛡️ TRADE BLOCKED",f"Symbol: {symbol}\nReason: {state.reason}"); continue
        result=submit_market_order(symbol,item.signal.action,1,client_order_id=f"tradingbot-{uuid4().hex[:20]}"); executed.append(result); journal(symbol,"executed",signal=item.signal,result=str(result)); notify("✅ ALPACA PAPER TRADE",f"Symbol: {symbol}\nAction: {item.signal.action}\nOrder submitted.")
    return AutoCycleResult(scanned,executed,skipped)
