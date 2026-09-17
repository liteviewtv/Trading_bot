"""Multi-asset automatic MT5 demo cycle with position/trade limits."""

from __future__ import annotations

from dataclasses import dataclass

from .mt5_multi_asset import AssetResult, DEFAULT_ASSETS, scan_assets
from .mt5_demo_cycle import run_demo_cycle
from .mt5_position_manager import inspect_positions
from .trade_journal import append_entry, make_entry


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
) -> AutoCycleResult:
    """Scan assets and optionally submit only permitted demo orders."""
    if max_orders < 0:
        raise ValueError("max_orders must be non-negative")
    if max_open_positions < 0:
        raise ValueError("max_open_positions must be non-negative")

    scanned = scan_assets(assets)
    executed: list[object] = []
    skipped: list[str] = []

    def journal(symbol, event, reason=None, signal=None, result=None):
        if journal_path is not None:
            append_entry(journal_path, make_entry(
                event, symbol, reason=reason,
                action=getattr(signal, "action", None), result=result,
            ))

    for item in scanned:
        symbol = item.symbol or item.requested
        if item.signal is None:
            reason = item.error or "No trading signal"
            skipped.append(f"{item.requested}: no signal")
            journal(symbol, "skipped", reason=reason)
            continue
        if not execute:
            skipped.append(f"{item.requested}: execution disabled")
            journal(symbol, "signal", reason="execution disabled", signal=item.signal)
            continue
        if len(executed) >= max_orders:
            skipped.append(f"{item.requested}: order limit reached")
            journal(symbol, "skipped", reason="order limit reached", signal=item.signal)
            continue

        state = inspect_positions(symbol, max_open_positions=max_open_positions)
        if not state.can_open:
            skipped.append(f"{item.requested}: {state.reason}")
            journal(symbol, "skipped", reason=state.reason, signal=item.signal)
            continue

        result = run_demo_cycle(symbol, execute=True)
        executed.append(result)
        journal(symbol, "executed", signal=item.signal, result=str(getattr(result, "message", result)))

    return AutoCycleResult(scanned, executed, skipped)
