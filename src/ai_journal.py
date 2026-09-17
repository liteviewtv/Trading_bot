"""Append-only JSONL journal for AI trading decisions."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def log_ai_decision(path, *, symbol, strategy_action, context, decision, confidence, reason, model):
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "symbol": symbol,
        "strategy_action": strategy_action,
        "market_context": context or {},
        "decision": decision,
        "confidence": float(confidence),
        "reason": reason,
        "model": model,
    }
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, separators=(",", ":"), default=str) + "\n")
    return record
