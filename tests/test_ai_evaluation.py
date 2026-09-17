import pytest

from src.ai_evaluation import evaluate_decision, summarize_evaluations


def test_buy_outcome():
    result = evaluate_decision("BUY", 100, 105)
    assert result["correct"] is True
    assert result["return_pct"] == pytest.approx(5.0)


def test_sell_outcome():
    result = evaluate_decision("SELL", 100, 95)
    assert result["correct"] is True
    assert result["return_pct"] == pytest.approx(5.0)


def test_summary():
    records = [evaluate_decision("BUY", 100, 105), evaluate_decision("SELL", 100, 102)]
    result = summarize_evaluations(records)
    assert result["count"] == 2
    assert result["accuracy_pct"] == 50.0
    assert result["avg_return_pct"] == pytest.approx(1.5)
