"""Minimal REST client for Alpaca paper trading and crypto market data."""
from __future__ import annotations
import os
import requests
from datetime import datetime, timedelta, timezone

PAPER_BASE_URL = "https://paper-api.alpaca.markets"
DATA_BASE_URL = "https://data.alpaca.markets"

def _keys():
    key=os.getenv("ALPACA_API_KEY","").strip(); secret=os.getenv("ALPACA_API_SECRET","").strip()
    if not key or not secret: raise RuntimeError("Set ALPACA_API_KEY and ALPACA_API_SECRET for the Alpaca paper account.")
    return key,secret

def _headers():
    key,secret=_keys(); return {"APCA-API-KEY-ID":key,"APCA-API-SECRET-KEY":secret}

def request(method,path,*,data=None,params=None):
    response=requests.request(method,f"{PAPER_BASE_URL}{path}",headers={**_headers(),"Content-Type":"application/json"},json=data,params=params,timeout=20)
    if not response.ok: raise RuntimeError(f"Alpaca API {response.status_code}: {response.text[:500]}")
    return response.json() if response.content else None

def account(): return request("GET","/v2/account")
def positions(): return request("GET","/v2/positions")

def available_instruments(asset_class="crypto"):
    return request("GET","/v2/assets",params={"status":"active","asset_class":asset_class}) or []

def crypto_universe(exclude_symbols=None):
    excluded=set(exclude_symbols or ())
    return [a["symbol"] for a in available_instruments("crypto")
            if a.get("status")=="active" and a.get("tradable")
            and "/" in a.get("symbol","") and a.get("symbol","").endswith("/USD")
            and a["symbol"] not in excluded]

def open_position(symbol):
    response=requests.get(f"{PAPER_BASE_URL}/v2/positions/{symbol}",headers=_headers(),timeout=20)
    if response.status_code==404: return None
    if not response.ok: raise RuntimeError(f"Alpaca API {response.status_code}: {response.text[:500]}")
    return response.json()

def bars(symbol,timeframe="15Min",limit=100):
    if "/" not in symbol: raise ValueError(f"Unsupported non-crypto symbol: {symbol}")
    end=datetime.now(timezone.utc)
    minutes=15 if timeframe.endswith("Min") else 1440
    start=end-timedelta(minutes=max(limit*minutes*2, 24*60))
    response=requests.get(f"{DATA_BASE_URL}/v1beta3/crypto/us/bars",headers=_headers(),
                          params={"symbols":symbol,"timeframe":timeframe,"limit":limit,
                                  "start":start.isoformat(),"end":end.isoformat(),"sort":"asc"},timeout=20)
    if not response.ok: raise RuntimeError(f"Alpaca crypto market data {response.status_code}: {response.text[:500]}")
    return (response.json().get("bars") or {}).get(symbol,[])

def tradable_asset(symbol):
    for asset in available_instruments("crypto"):
        if asset.get("symbol")==symbol: return asset if asset.get("tradable") else None
    return None

def submit_market_order(symbol,side,qty=None,notional=None,client_order_id=None):
    payload={"symbol":symbol,"side":side.lower(),"type":"market","time_in_force":"gtc"}
    if notional is not None:
        if notional < 10:
            raise ValueError("Alpaca notional must be at least $10.")
        payload["notional"]=str(notional)
    elif qty is not None:
        payload["qty"]=str(qty)
    else:
        raise ValueError("Provide either qty or notional.")
    if client_order_id: payload["client_order_id"]=client_order_id
    return request("POST","/v2/orders",data=payload)
