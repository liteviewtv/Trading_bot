"""Minimal REST client for Alpaca paper trading and market data."""
from __future__ import annotations
import os
import requests

PAPER_BASE_URL = "https://paper-api.alpaca.markets"
DATA_BASE_URL = "https://data.alpaca.markets"

def _keys():
    key = os.getenv("ALPACA_API_KEY", "").strip()
    secret = os.getenv("ALPACA_API_SECRET", "").strip()
    if not key or not secret:
        raise RuntimeError("Set ALPACA_API_KEY and ALPACA_API_SECRET for the Alpaca paper account.")
    return key, secret

def _headers():
    key, secret = _keys()
    return {"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": secret}

def request(method, path, *, data=None, params=None):
    response = requests.request(method, f"{PAPER_BASE_URL}{path}", headers={**_headers(), "Content-Type": "application/json"}, json=data, params=params, timeout=20)
    if not response.ok:
        raise RuntimeError(f"Alpaca API {response.status_code}: {response.text[:500]}")
    return response.json() if response.content else None

def account(): return request("GET", "/v2/account")
def positions(): return request("GET", "/v2/positions")

def open_position(symbol):
    response = requests.get(f"{PAPER_BASE_URL}/v2/positions/{symbol}", headers=_headers(), timeout=20)
    if response.status_code == 404: return None
    if not response.ok: raise RuntimeError(f"Alpaca API {response.status_code}: {response.text[:500]}")
    return response.json()

def bars(symbol, timeframe="15Min", limit=100):
    response = requests.get(f"{DATA_BASE_URL}/v2/stocks/{symbol}/bars", headers=_headers(), params={"timeframe": timeframe, "limit": limit, "feed": "iex"}, timeout=20)
    if not response.ok: raise RuntimeError(f"Alpaca market data {response.status_code}: {response.text[:500]}")
    return response.json().get("bars", [])

def tradable_asset(symbol):
    response = requests.get(f"{PAPER_BASE_URL}/v2/assets/{symbol}", headers=_headers(), timeout=20)
    if response.status_code == 404: return None
    if not response.ok: raise RuntimeError(f"Alpaca asset API {response.status_code}: {response.text[:500]}")
    return response.json()

def submit_market_order(symbol, side, qty, client_order_id=None):
    payload = {"symbol": symbol, "qty": str(qty), "side": side.lower(), "type": "market", "time_in_force": "day"}
    if client_order_id: payload["client_order_id"] = client_order_id
    return request("POST", "/v2/orders", data=payload)
