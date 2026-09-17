"""Multi-asset automatic MT5 demo cycle with position/trade limits."""

from __future__ import annotations

from dataclasses import dataclass

from .mt5_multi_asset import AssetResult, DEFAULT_ASSETS, scan_assets
from .mt5_demo_cycle import run_demo_cycle
from .mt5_position_manager import inspect_positions


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
) -> AutoCycleResult:
    """Scan assets and optionally submit only permitted demo orders."""
    if max_orders < 0:
        raise ValueError("max_orders must be non-negative")
    if max_open_positions < 0:
        raise ValueError("max_open_positions must be non-negative")

    scanned = scan_assets(assets)
    executed: list[object] = []
    skipped: list[str] = []

    for item in scanned:
        if item.signal is None:
            skipped.append(f"{item.requested}: no signal")
            continue
        if not execute:
            skipped.append(f"{item.requested}: execution disabled")
            continue
        if len(executed) >= max_orders:
            skipped.append(f"{item.requested}: order limit reached")
            continue

        state = inspect_positions(item.symbol or item.requested, max_open_positions=max_open_positions)
        if not state.can_open:
            skipped.append(f"{item.requested}: {state.reason}")
            continue

        result = run_demo_cycle(item.symbol or item.requested, execute=True)
        executed.append(result)

    return AutoCycleResult(scanned, executed, skipped)
