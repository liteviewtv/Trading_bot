"""SQLite trade and event journal."""

import sqlite3
from pathlib import Path
from typing import Any


class TradeStore:
    def __init__(self, path: str = "trading_bot.sqlite3"):
        self.path = Path(path)
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.path)

    def _init_db(self):
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                qty INTEGER NOT NULL,
                entry_price REAL,
                exit_price REAL,
                status TEXT NOT NULL,
                pnl REAL,
                order_id TEXT,
                reason TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                closed_at TEXT
            )""")
            db.execute("""CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                level TEXT NOT NULL,
                event TEXT NOT NULL,
                details TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )""")

    def record_event(self, level: str, event: str, details: str = ""):
        with self._connect() as db:
            db.execute("INSERT INTO events(level,event,details) VALUES(?,?,?)", (level, event, details))

    def record_trade(self, symbol: str, side: str, qty: int, status: str,
                     entry_price: float | None = None, order_id: str | None = None,
                     reason: str = "") -> int:
        with self._connect() as db:
            cur = db.execute(
                "INSERT INTO trades(symbol,side,qty,entry_price,status,order_id,reason) VALUES(?,?,?,?,?,?,?)",
                (symbol, side, qty, entry_price, status, order_id, reason),
            )
            return int(cur.lastrowid)

    def close_trade(self, trade_id: int, exit_price: float, pnl: float, status: str = "CLOSED"):
        with self._connect() as db:
            db.execute(
                "UPDATE trades SET exit_price=?, pnl=?, status=?, closed_at=CURRENT_TIMESTAMP WHERE id=?",
                (exit_price, pnl, status, trade_id),
            )
