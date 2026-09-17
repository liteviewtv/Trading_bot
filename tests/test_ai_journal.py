import json

from src.ai_journal import log_ai_decision


def test_log_ai_decision(tmp_path):
    path = tmp_path / "ai.jsonl"
    record = log_ai_decision(
        path,
        symbol="EURUSD",
        strategy_action="BUY",
        context={"close": 1.1},
        decision="BUY",
        confidence=0.82,
        reason="trend",
        model="groq",
    )
    assert record["symbol"] == "EURUSD"
    saved = json.loads(path.read_text())
    assert saved["confidence"] == 0.82
    assert saved["decision"] == "BUY"
