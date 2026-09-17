from src.ai_signal import AIAnalysis
from src.groq_ai import GroqAnalyzer


def test_groq_requires_key():
    try:
        GroqAnalyzer(api_key=None).analyze(type("S", (), {"action": "BUY"})())
    except RuntimeError as exc:
        assert "GROQ_API_KEY" in str(exc)
    else:
        raise AssertionError("missing API key must fail safely")


def test_groq_parses_json_response(monkeypatch):
    class Response:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self):
            return b'{"choices":[{"message":{"content":"{\\"decision\\":\\"BUY\\",\\"confidence\\":0.81,\\"reason\\":\\"trend\\"}"}}]}'

    monkeypatch.setattr("src.groq_ai.urlopen", lambda *args, **kwargs: Response())
    result = GroqAnalyzer(api_key="test-key").analyze(type("S", (), {"action": "BUY"})())
    assert result == AIAnalysis("BUY", 0.81, "trend", "openai/gpt-oss-120b")
