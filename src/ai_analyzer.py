"""AI advisory analyzer using an OpenAI-compatible local endpoint (Ollama by default)."""
from __future__ import annotations
import json, os, requests
from dataclasses import dataclass

@dataclass(frozen=True)
class AIAnalysis:
    decision: str
    confidence: float
    reason: str

class AIAnalyzer:
    def __init__(self, base_url=None, model=None, timeout=20):
        self.base_url=(base_url or os.getenv("AI_BASE_URL","http://127.0.0.1:11434/v1")).rstrip("/")
        self.model=model or os.getenv("AI_MODEL","llama3.2:3b")
        self.timeout=timeout

    def analyze(self, signal, context):
        payload={"model":self.model,"temperature":0,"messages":[
            {"role":"system","content":"You are a conservative crypto trading signal reviewer. Return ONLY valid JSON with keys decision, confidence, reason. decision must be BUY, SELL, or HOLD. Never invent market data. Review the supplied strategy signal; you may reject it but cannot override risk controls."},
            {"role":"user","content":json.dumps({"symbol":str(context.get("symbol","")),"strategy_action":getattr(signal,"action",None),"price":getattr(signal,"price",None),"strategy_reason":getattr(signal,"reason",None),"context":context})}
        ]}
        r=requests.post(f"{self.base_url}/chat/completions",json=payload,timeout=self.timeout)
        r.raise_for_status()
        content=r.json()["choices"][0]["message"]["content"].strip()
        if content.startswith("```"):
            content=content.strip("`")
            if content.startswith("json"): content=content[4:].strip()
        data=json.loads(content)
        decision=str(data["decision"]).upper(); confidence=float(data["confidence"]); reason=str(data["reason"])
        if decision not in {"BUY","SELL","HOLD"} or not 0 <= confidence <= 1: raise ValueError("Invalid AI response")
        return AIAnalysis(decision,confidence,reason)
