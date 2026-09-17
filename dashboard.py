"""Minimal local Streamlit dashboard for the paper bot."""

import os
import sqlite3

import streamlit as st

st.set_page_config(page_title="Trading Bot", page_icon="📈", layout="wide")
st.title("📈 Trading Bot")
st.caption("Paper-trading monitor — live trading is disabled by design.")

DB_PATH = os.getenv("TRADING_BOT_DB", "trading_bot.sqlite3")

try:
    with sqlite3.connect(DB_PATH) as db:
        trades = db.execute(
            "SELECT symbol, side, qty, entry_price, exit_price, status, pnl, reason, created_at "
            "FROM trades ORDER BY id DESC LIMIT 100"
        ).fetchall()
        events = db.execute(
            "SELECT level, event, details, created_at FROM events ORDER BY id DESC LIMIT 50"
        ).fetchall()
except sqlite3.Error as exc:
    st.error(f"Database error: {exc}")
    st.stop()

closed_pnl = sum((row[6] or 0) for row in trades if row[5] == "CLOSED")
open_count = sum(1 for row in trades if row[5] not in ("CLOSED", "CANCELLED"))

c1, c2, c3 = st.columns(3)
c1.metric("Recorded closed P&L", f"${closed_pnl:,.2f}")
c2.metric("Open/active records", open_count)
c3.metric("Recorded trades", len(trades))

st.subheader("Recent trades")
st.dataframe(
    trades,
    column_config={
        "symbol": "Symbol", "side": "Side", "qty": "Qty", "entry_price": "Entry",
        "exit_price": "Exit", "status": "Status", "pnl": "P&L", "reason": "Reason", "created_at": "Created"
    },
    use_container_width=True,
)

st.subheader("Recent bot events")
st.dataframe(events, use_container_width=True)
