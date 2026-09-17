"""Optional Groq API adapter for AI-assisted signal analysis."""

from __future__ import annotations

import json
import os
from urllib.request import Request, urlopen

from .ai_signal import AIAnalysis


GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


class GroqAnalyzer:
    def __init__(self, api_key: str | None = None, model: str = "openai/gpt-oss-120b", timeout: float = 15.0):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.model = model
        self.timeout = timeout

    def analyze(self, signal, context: dict | None = None) -> AIAnalysis:
        if not self.api_key:
            raise RuntimeError("GROQ_API_KEY is not configured")
        market_context = context or {}
        payload = {
            "model": self.model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": "You are a cautious trading-signal analyst. Analyze the strategy signal together with the supplied market context. Return JSON with decision (BUY, SELL, HOLD), confidence (0 to 1), and reason. Never claim certainty. Do not provide position sizing, override risk rules, or place orders."},
                {"role": "user", "content": json.dumps({"strategy_signal": getattr(signal, "action", None), "market_context": market_context}, default=str)},
            ],
        }
        request = Request(GROQ_URL, data=json.dumps(payload).encode(), headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}, method="POST")
        with urlopen(request, timeout=self.timeout) as response:
            data = json.loads(response.read().decode())
        content = data["choices"][0]["message"]["content"]
        result = json.loads(content)
        decision = str(result.get("decision", "HOLD")).upper()
        confidence = float(result.get("confidence", 0.0))
        if decision not in {"BUY", "SELL", "HOLD"} or not 0 <= confidence <= 1:
            raise ValueError("Invalid Groq AI response")
        return AIAnalysis(decision, confidence, str(result.get("reason", "")), self.model)
