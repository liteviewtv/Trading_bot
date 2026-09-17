"""JSONL trade journal for signals, skips, executions, and outcomes."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class JournalEntry:
    event: str
    symbol: str
    timestamp: str
    reason: str | None = None
    action: str | None = None
    entry: float | None = None
    stop_loss: float | None = None
    take_profit: float | None = None
    result: str | None = None
    metadata: dict[str, Any] | None = None


def make_entry(event: str, symbol: str, **kwargs: Any) -> JournalEntry:
    return JournalEntry(event=event, symbol=symbol, timestamp=datetime.now(timezone.utc).isoformat(), **kwargs)


def append_entry(path: str | Path, entry: JournalEntry) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(entry), separators=(",", ":")) + "\n")


def read_entries(path: str | Path) -> list[JournalEntry]:
    target = Path(path)
    if not target.exists():
        return []
    entries: list[JournalEntry] = []
    for line in target.read_text(encoding="utf-8").splitlines():
        if line.strip():
            entries.append(JournalEntry(**json.loads(line)))
    return entries
