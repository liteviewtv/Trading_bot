"""Alpaca-backed automatic paper-trading cycle."""
from dataclasses import dataclass
from datetime import datetime, timezone
from time import monotonic
import logging
from .ai_filter import AIFilterDecision, filter_signal
from .alpaca_client import bars, positions, open_orders, submit_market_order, close_position, tradable_asset
from .alpaca_position_manager import inspect_positions
from .alpaca_strategy import generate_alpaca_signal, candles_to_dataframe
from .strategy import diagnose_signal
from .trade_journal import append_entry, make_entry
from .telegram_notify import TelegramNotifier

log = logging.getLogger(__name__)
_AI_FAILURE_ALERT_ACTIVE = False
_BLOCK_ALERT_LAST: dict[tuple[str, str], float] = {}
_ORDER_BUCKET_SECONDS = 1800

@dataclass(frozen=True)
class AssetResult:
    requested: str
    symbol: str | None
    signal: object | None
    error: str | None = None
    diagnostic: str | None = None
    context: dict | None = None

@dataclass(frozen=True)
class AutoCycleResult:
    scanned: list[AssetResult]
    executed: list[object]
    skipped: list[str]

def _market_context(frame, sma_period, breakout_lookback):
    if frame.empty or len(frame) < max(sma_period, breakout_lookback) + 1:
        return {}
    data = frame.copy()
    data["sma"] = data["close"].rolling(sma_period).mean()
    latest = data.iloc[-1]
    previous = data.iloc[-2]
    prior = data.iloc[-breakout_lookback-1:-1]
    close = float(latest["close"])
    previous_close = float(previous["close"])
    sma = float(latest["sma"])
    prior_high = float(prior["high"].max())
    prior_low = float(prior["low"].min())
    ret = (close / previous_close - 1) * 100 if previous_close else 0.0
    sma_distance = (close / sma - 1) * 100 if sma else 0.0
    sma_5 = float(data["sma"].iloc[-6]) if len(data) >= sma_period + 5 else sma
    sma_slope = (sma / sma_5 - 1) * 100 if sma_5 else 0.0
    context = {
        "timeframe": "15Min",
        "latest_close": close,
        "previous_close": previous_close,
        "sma": sma,
        "sma_distance_pct": sma_distance,
        "sma_slope_5bars_pct": sma_slope,
        "prior_high": prior_high,
        "prior_low": prior_low,
        "return_pct": ret,
        "high_breakout": close > prior_high,
        "low_breakout": close < prior_low,
        "above_sma": close > sma,
        "below_sma": close < sma,
    }
    if "v" in data.columns:
        volume = float(latest["v"])
        avg_volume = float(data["v"].iloc[-21:-1].mean()) if len(data) >= 22 else volume
        context["volume"] = volume
        context["avg_volume_20"] = avg_volume
        context["volume_ratio"] = volume / avg_volume if avg_volume else 0.0
    return context

def scan_assets(assets, *, min_return_pct=0.1, sma_period=50, breakout_lookback=20):
    results=[]
    for symbol in assets:
        try:
            asset=tradable_asset(symbol)
            if not asset or not asset.get("tradable"):
                results.append(AssetResult(symbol,None,None,"Asset unavailable or not tradable")); continue
            raw_bars=bars(symbol)
            frame=candles_to_dataframe(raw_bars)
            market_context=_market_context(frame,sma_period,breakout_lookback)
            signal=generate_alpaca_signal(symbol,raw_bars,sma_period=sma_period,breakout_lookback=breakout_lookback,min_return_pct=min_return_pct)
            diagnostic=None if signal is not None else diagnose_signal(symbol,frame,sma_period=sma_period,breakout_lookback=breakout_lookback,min_return_pct=min_return_pct)
            results.append(AssetResult(symbol,symbol,signal,diagnostic=diagnostic,context=market_context))
        except Exception as exc:
            results.append(AssetResult(symbol,symbol,None,str(exc)))
    return results

def _client_order_id(symbol, action, signal):
    clean = symbol.replace("/", "-").replace("_", "-")
    bar_key = "signal"
    reason = getattr(signal, "reason", "")
    if reason:
        bar_key = str(abs(hash(reason)))[:10]
    bucket = int(monotonic() // _ORDER_BUCKET_SECONDS)
    return f"tb-{action.lower()}-{clean}-{bucket}-{bar_key}"[:128]

def _notify_block(notifier, symbol, reason):
    key=(symbol,reason)
    now=monotonic()
    if now-_BLOCK_ALERT_LAST.get(key,0) >= _ORDER_BUCKET_SECONDS:
        _BLOCK_ALERT_LAST[key]=now
        try: notifier.event("🛡️ TRADE BLOCKED",f"Symbol: {symbol}\nReason: {reason}")
        except Exception: pass

def manage_open_positions(*, stop_loss_pct, take_profit_pct, notifier, journal):
    """Protect existing long positions; crypto does not use bracket orders here."""
    try:
        current=list(positions())
        pending={str(o.get("symbol","")) for o in open_orders() if str(o.get("status","")).lower() in {"new","accepted","pending_new","partially_filled"}}
    except Exception as exc:
        log.warning("Position protection check failed: %s", exc)
        return []
    actions=[]
    for position in current:
        symbol=str(position.get("symbol",""))
        if not symbol or symbol in pending: continue
        try:
            frame=candles_to_dataframe(bars(symbol,limit=3))
            if frame.empty: continue
            price=float(frame.iloc[-1]["close"])
            entry=float(position.get("avg_entry_price") or 0)
            if entry <= 0: continue
            pnl_pct=(price/entry-1)*100
            reason=None
            if pnl_pct <= -abs(stop_loss_pct): reason=f"stop loss hit ({pnl_pct:.2f}%)"
            elif pnl_pct >= abs(take_profit_pct): reason=f"take profit hit ({pnl_pct:.2f}%)"
            if reason:
                result=close_position(symbol)
                actions.append(result)
                journal(symbol,"closed",reason=reason,result=str(result))
                log.info("Position closed | symbol=%s | price=%.6f | pnl=%.2f%% | reason=%s",symbol,price,pnl_pct,reason)
                try: notifier.event("🛡️ POSITION CLOSED",f"Symbol: {symbol}\nPnL: {pnl_pct:.2f}%\nReason: {reason}")
                except Exception: pass
        except Exception as exc:
            log.warning("Position protection failed | symbol=%s | error=%s",symbol,exc)
    return actions

def run_auto_demo_cycle(assets, execute=False, max_orders=2, max_open_positions=5, min_return_pct=0.1, sma_period=50, breakout_lookback=20, journal_path=None, ai_decisions=None, ai_min_confidence=0.60, ai_analyzer=None, notifier=None, control=None, stop_loss_pct=1.5, take_profit_pct=3.0):
    global _AI_FAILURE_ALERT_ACTIVE
    if max_orders < 0 or max_open_positions < 0: raise ValueError("position/order limits must be non-negative")
    notifier=notifier or TelegramNotifier()
    scanned=scan_assets(assets,min_return_pct=min_return_pct,sma_period=sma_period,breakout_lookback=breakout_lookback)
    executed=[]; skipped=[]; ai_failures=[]
    def journal(symbol,event,reason=None,signal=None,result=None):
        if journal_path is not None: append_entry(journal_path,make_entry(event,symbol,reason=reason,action=getattr(signal,"action",None),result=result))
    def notify(event,details=""):
        try: notifier.event(event,details)
        except Exception: pass
    if execute and control is not None and getattr(control,"paused",False): return AutoCycleResult(scanned,executed,["paper trading paused"])
    if execute:
        manage_open_positions(stop_loss_pct=stop_loss_pct,take_profit_pct=take_profit_pct,notifier=notifier,journal=journal)
    for item in scanned:
        symbol=item.symbol or item.requested
        if item.signal is None:
            reason=item.error or "No trading signal"; skipped.append(f"{item.requested}: no signal"); journal(symbol,"skipped",reason=reason)
            log.info("Signal rejected | symbol=%s | reason=%s | diagnostic=%s",symbol,reason,item.diagnostic or "n/a")
            if reason not in {"Asset unavailable or not tradable","No trading signal"}: notify("⚠️ SIGNAL SKIPPED",f"Symbol: {symbol}\nReason: {reason}")
            continue
        log.info("Signal generated | symbol=%s | action=%s | price=%.4f | reason=%s",symbol,item.signal.action,float(item.signal.price),item.signal.reason)
        if not execute:
            skipped.append(f"{item.requested}: execution disabled"); journal(symbol,"signal",reason="execution disabled",signal=item.signal); notify("🤖 PAPER SIGNAL",f"Symbol: {symbol}\nAction: {item.signal.action}\nMode: Alpaca paper"); continue
        if len(executed) >= max_orders:
            skipped.append(f"{item.requested}: order limit reached"); journal(symbol,"skipped",reason="order limit reached",signal=item.signal); log.info("Trade rejected | symbol=%s | reason=order limit reached",symbol); continue
        if ai_analyzer is not None:
            try:
                context={"symbol":symbol,"strategy_action":item.signal.action,"price":float(item.signal.price),"strategy_reason":item.signal.reason,"market":item.context or {}}
                analysis=ai_analyzer.analyze(item.signal,context)
                ai_decisions=dict(ai_decisions or {})
                ai_decisions[symbol]=AIFilterDecision(str(analysis.decision).upper(),float(analysis.confidence),str(analysis.reason))
                if _AI_FAILURE_ALERT_ACTIVE:
                    notify("✅ AI ANALYSIS RECOVERED","Groq AI is responding again."); _AI_FAILURE_ALERT_ACTIVE=False
            except Exception as exc:
                ai_failures.append((symbol,str(exc))); skipped.append(f"{item.requested}: AI analysis failed"); journal(symbol,"skipped",reason=f"AI analysis failed: {exc}",signal=item.signal); log.info("Trade rejected | symbol=%s | reason=AI analysis failed: %s",symbol,exc); continue
        if ai_decisions is not None:
            decision=ai_decisions.get(symbol) or ai_decisions.get(item.requested)
            if decision is None: skipped.append(f"{item.requested}: AI decision unavailable"); journal(symbol,"skipped",reason="AI decision unavailable",signal=item.signal); log.info("Trade rejected | symbol=%s | reason=AI decision unavailable",symbol); continue
            filtered=filter_signal(item.signal,decision,ai_min_confidence)
            if filtered.action == "HOLD":
                skipped.append(f"{item.requested}: {filtered.reason}"); journal(symbol,"skipped",reason=filtered.reason,signal=item.signal); log.info("Trade rejected | symbol=%s | reason=%s",symbol,filtered.reason); notify("⏸️ TRADE REJECTED",f"Symbol: {symbol}\nReason: {filtered.reason}"); continue
        # SELL signals close an existing long; BUY signals require a new position slot.
        existing=next((p for p in positions() if str(p.get("symbol",""))==symbol),None) if item.signal.action=="SELL" else None
        if item.signal.action=="SELL":
            if existing is None:
                skipped.append(f"{item.requested}: no position to sell"); continue
            try:
                result=close_position(symbol); executed.append(result); journal(symbol,"executed",reason="strategy SELL",signal=item.signal,result=str(result)); notify("🔻 ALPACA PAPER EXIT",f"Symbol: {symbol}\nAction: SELL\nPosition closed.")
            except Exception as exc:
                skipped.append(f"{item.requested}: exit failed"); log.warning("Exit failed | symbol=%s | error=%s",symbol,exc)
            continue
        state=inspect_positions(symbol,max_open_positions=max_open_positions)
        if not state.can_open:
            skipped.append(f"{item.requested}: {state.reason}"); journal(symbol,"skipped",reason=state.reason,signal=item.signal); log.info("Trade rejected | symbol=%s | reason=%s",symbol,state.reason); _notify_block(notifier,symbol,state.reason); continue
        try:
            client_id=_client_order_id(symbol,item.signal.action,item.signal)
            result=submit_market_order(symbol,item.signal.action,notional=25,client_order_id=client_id)
        except Exception as exc:
            skipped.append(f"{item.requested}: order submission failed"); journal(symbol,"skipped",reason=f"order submission failed: {exc}",signal=item.signal); log.warning("Order submission failed | symbol=%s | error=%s",symbol,exc); continue
        executed.append(result); journal(symbol,"executed",signal=item.signal,result=str(result)); notify("✅ ALPACA PAPER TRADE",f"Symbol: {symbol}\nAction: {item.signal.action}\nOrder submitted.")
    if ai_failures and not _AI_FAILURE_ALERT_ACTIVE:
        symbols=", ".join(symbol for symbol,_ in ai_failures[:8]); suffix=f" (+{len(ai_failures)-8} more)" if len(ai_failures)>8 else ""
        notify("❌ GROQ AI UNAVAILABLE",f"AI analysis failed for {len(ai_failures)} signal(s).\nSymbols: {symbols}{suffix}\nTrading was blocked for those signals. Telegram alerts are suppressed until Groq recovers."); _AI_FAILURE_ALERT_ACTIVE=True
    return AutoCycleResult(scanned,executed,skipped)
