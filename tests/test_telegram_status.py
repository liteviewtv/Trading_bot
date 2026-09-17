from src.telegram_notify import TelegramNotifier
from src.telegram_status import respond_to_update, status_for_journal


def test_status_for_journal(tmp_path):
    journal = tmp_path / "paper.jsonl"
    journal.write_text('{"type":"paper_outcome","symbol":"EURUSD","decision":"BUY","confidence":0.8,"entry":100,"exit":105}\n')
    text = status_for_journal(journal)
    assert "Trades: 1" in text
    assert "Win rate: 100.0%" in text


def test_respond_to_status_update(tmp_path, monkeypatch):
    journal = tmp_path / "paper.jsonl"
    sent = []
    notifier = TelegramNotifier(token="token", chat_id="chat")
    monkeypatch.setattr(notifier, "send", lambda message: sent.append(message) or True)
    handled = respond_to_update({"message": {"text": "/status"}}, journal_path=journal, notifier=notifier)
    assert handled
    assert "PAPER TRADING STATUS" in sent[0]


def test_ignores_other_updates(tmp_path):
    assert not respond_to_update({"message": {"text": "/help"}}, journal_path=tmp_path / "paper.jsonl", notifier=TelegramNotifier())
