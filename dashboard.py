"""Streamlit dashboard for paper-trading performance and monitoring."""

import os
import sqlite3

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Trading Bot", page_icon="📈", layout="wide")
st.title("📈 Trading Bot Dashboard")
st.caption("Paper-trading monitor — live trading is disabled by design.")

DB_PATH = os.getenv("TRADING_BOT_DB", "trading_bot.sqlite3")

try:
    with sqlite3.connect(DB_PATH) as db:
        trades = pd.read_sql_query(
            "SELECT symbol, side, qty, entry_price, exit_price, status, pnl, reason, created_at, closed_at "
            "FROM trades ORDER BY id DESC LIMIT 500", db)
        events = pd.read_sql_query(
            "SELECT level, event, details, created_at FROM events ORDER BY id DESC LIMIT 100", db)
except sqlite3.Error as exc:
    st.error(f"Database error: {exc}")
    st.stop()

closed = trades[trades["status"] == "CLOSED"].copy()
closed["pnl"] = pd.to_numeric(closed["pnl"], errors="coerce").fillna(0)
net_pnl = float(closed["pnl"].sum())
win_rate = float((closed["pnl"] > 0).mean() * 100) if len(closed) else 0.0
wins = float(closed.loc[closed["pnl"] > 0, "pnl"].sum())
losses = abs(float(closed.loc[closed["pnl"] < 0, "pnl"].sum()))
profit_factor = wins / losses if losses else (float("inf") if wins else 0.0)

equity = 0.0
peak = 0.0
max_drawdown = 0.0
curve = []
for pnl in closed.sort_values("closed_at")["pnl"].tolist():
    equity += float(pnl)
    peak = max(peak, equity)
    dd = peak - equity
    max_drawdown = max(max_drawdown, dd)
    curve.append(equity)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Net P&L", f"${net_pnl:,.2f}")
c2.metric("Win rate", f"{win_rate:.1f}%")
c3.metric("Profit factor", f"{profit_factor:.2f}")
c4.metric("Max drawdown", f"${max_drawdown:,.2f}")

if curve:
    st.subheader("Equity curve")
    st.line_chart(pd.DataFrame({"Cumulative P&L": curve}))

st.subheader("Recent trades")
st.dataframe(closed.head(100), use_container_width=True)

st.subheader("Recent bot events")
st.dataframe(events, use_container_width=True)
