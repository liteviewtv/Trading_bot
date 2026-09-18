"""Groq-backed AI advisory signal analyzer."""
from __future__ import annotations

import json
import os
from dataclasses import dataclass

import requests


@dataclass(frozen=True)
class AIAnalysis:
    decision: str
    confidence: float
    reason: str


class AIAnalyzer:
    def __init__(self, api_key=None, model=None, timeout=20):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.base_url = "https://api.groq.com/openai/v1"
        self.model = model or os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
        self.timeout = timeout
        if not self.api_key:
            raise RuntimeError("GROQ_API_KEY is not configured")

    def _headers(self):
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    @staticmethod
    def _extract_json_text(data):
        output_text = data.get("output_text")
        if isinstance(output_text, str) and output_text.strip():
            return output_text.strip()
        for item in data.get("output", []) or []:
            for content in item.get("content", []) or []:
                if content.get("type") in {"output_text", "text"}:
                    text = content.get("text")
                    if isinstance(text, str) and text.strip():
                        return text.strip()
        choices = data.get("choices", []) or []
        if choices:
            content = choices[0].get("message", {}).get("content")
            if isinstance(content, str) and content.strip():
                return content.strip()
        raise ValueError("Groq response did not contain model text")

    @staticmethod
    def _parse_analysis(content):
        content = content.strip()
        if content.startswith("```"):
            content = content.strip("`").strip()
            if content.lower().startswith("json"):
                content = content[4:].strip()
        data = json.loads(content)
        decision = str(data["decision"]).upper()
        confidence = float(data["confidence"])
        reason = str(data["reason"])
        if decision not in {"BUY", "SELL", "HOLD"} or not 0 <= confidence <= 1:
            raise ValueError("Invalid AI response")
        return AIAnalysis(decision, confidence, reason)

    def _context_payload(self, signal, context):
        return json.dumps({
            "symbol": str(context.get("symbol", "")),
            "strategy_action": getattr(signal, "action", None),
            "price": getattr(signal, "price", None),
            "strategy_reason": getattr(signal, "reason", None),
            "context": context,
        }, default=str)

    def _analyze_responses(self, signal, context):
        payload = {
            "model": self.model,
            "instructions": ("You are a conservative crypto trading signal reviewer. Return ONLY valid JSON with keys decision, confidence, reason. decision must be BUY, SELL, or HOLD. Never invent market data. The strategy signal is the primary signal; approve only when the supplied evidence supports it. Do not override risk controls."),
            "input": self._context_payload(signal, context),
        }
        response = requests.post(f"{self.base_url}/responses", headers=self._headers(), json=payload, timeout=self.timeout)
        response.raise_for_status()
        return self._parse_analysis(self._extract_json_text(response.json()))

    def _analyze_chat(self, signal, context):
        payload = {
            "model": self.model,
            "temperature": 0,
            "messages": [
                {"role": "system", "content": "You are a conservative crypto trading signal reviewer. Return ONLY valid JSON with keys decision, confidence, reason. decision must be BUY, SELL, or HOLD. Never invent market data. The strategy signal is the primary signal; approve only when the supplied evidence supports it. Do not override risk controls."},
                {"role": "user", "content": self._context_payload(signal, context)},
            ],
        }
        response = requests.post(f"{self.base_url}/chat/completions", headers=self._headers(), json=payload, timeout=self.timeout)
        response.raise_for_status()
        return self._parse_analysis(self._extract_json_text(response.json()))

    def analyze(self, signal, context):
        try:
            return self._analyze_responses(signal, context)
        except requests.HTTPError as responses_error:
            try:
                return self._analyze_chat(signal, context)
            except Exception as chat_error:
                raise RuntimeError(f"Groq Responses API failed ({responses_error}); Chat Completions fallback failed ({chat_error})") from chat_error
