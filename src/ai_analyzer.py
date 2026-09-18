"""Groq-backed AI advisory signal analyzer."""
from __future__ import annotations
import json, os, requests
from dataclasses import dataclass

@dataclass(frozen=True)
class AIAnalysis:
    decision: str
    confidence: float
    reason: str

class AIAnalyzer:
    def __init__(self, api_key=None, model=None, timeout=20):
        self.api_key=api_key or os.getenv("GROQ_API_KEY")
        self.base_url="https://api.groq.com/openai/v1"
        self.model=model or os.getenv("GROQ_MODEL","openai/gpt-oss-20b")
        self.timeout=timeout
        if not self.api_key: raise RuntimeError("GROQ_API_KEY is not configured")

    def analyze(self, signal, context):
        payload={"model":self.model,"temperature":0,"messages":[
            {"role":"system","content":"You are a conservative crypto trading signal reviewer. Return ONLY valid JSON with keys decision, confidence, reason. decision must be BUY, SELL, or HOLD. Never invent market data. The strategy signal is the primary signal; approve only when the supplied evidence supports it. Do not override risk controls."},
            {"role":"user","content":json.dumps({"symbol":str(context.get("symbol","")),"strategy_action":getattr(signal,"action",None),"price":getattr(signal,"price",None),"strategy_reason":getattr(signal,"reason",None),"context":context})}
        ]}
        r=requests.post(f"{self.base_url}/chat/completions",headers={"Authorization":f"Bearer {self.api_key}","Content-Type":"application/json"},json=payload,timeout=self.timeout)
        r.raise_for_status()
        content=r.json()["choices"][0]["message"]["content"].strip()
        if content.startswith("```"):
            content=content.strip("`")
            if content.startswith("json"): content=content[4:].strip()
        data=json.loads(content)
        decision=str(data["decision"]).upper(); confidence=float(data["confidence"]); reason=str(data["reason"])
        if decision not in {"BUY","SELL","HOLD"} or not 0 <= confidence <= 1: raise ValueError("Invalid AI response")
        return AIAnalysis(decision,confidence,reason)
