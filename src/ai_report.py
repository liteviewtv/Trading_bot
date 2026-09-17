"""Build performance summaries from AI journal records."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path


def build_ai_report(path) -> dict:
    decisions = []
    outcomes = []
    for line in Path(path).read_text(encoding="utf-8").splitlines() if Path(path).exists() else []:
        if not line.strip():
            continue
        record = json.loads(line)
        (outcomes if record.get("type") == "paper_outcome" else decisions).append(record)

    actionable = [d for d in decisions if d.get("decision") in {"BUY", "SELL"}]
    by_symbol = defaultdict(list)
    for outcome in outcomes:
        by_symbol[outcome.get("symbol")].append(outcome)

    report = {
        "decisions": len(decisions),
        "buy": sum(d.get("decision") == "BUY" for d in decisions),
        "sell": sum(d.get("decision") == "SELL" for d in decisions),
        "hold": sum(d.get("decision") == "HOLD" for d in decisions),
        "actionable": len(actionable),
        "outcomes": len(outcomes),
        "wins": sum(bool(o.get("win")) for o in outcomes),
        "losses": sum(not bool(o.get("win")) for o in outcomes),
        "win_rate_pct": round(sum(bool(o.get("win")) for o in outcomes) / len(outcomes) * 100, 4) if outcomes else 0.0,
        "average_confidence": round(sum(float(d.get("confidence", 0)) for d in decisions) / len(decisions), 4) if decisions else 0.0,
        "average_pnl_pct": round(sum(float(o.get("pnl_pct", 0)) for o in outcomes) / len(outcomes), 4) if outcomes else 0.0,
        "by_symbol": {},
    }
    for symbol, rows in by_symbol.items():
        report["by_symbol"][symbol] = {
            "trades": len(rows),
            "wins": sum(bool(r.get("win")) for r in rows),
            "average_pnl_pct": round(sum(float(r.get("pnl_pct", 0)) for r in rows) / len(rows), 4),
        }
    return report
