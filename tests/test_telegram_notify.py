from src.telegram_notify import TelegramNotifier


def test_unconfigured_notifier_is_safe():
    notifier = TelegramNotifier(token=None, chat_id=None)
    assert not notifier.configured
    assert notifier.send("test") is False


def test_signal_message_uses_send(monkeypatch):
    notifier = TelegramNotifier(token="token", chat_id="chat")
    sent = []
    monkeypatch.setattr(notifier, "send", lambda message: sent.append(message) or True)
    assert notifier.signal("EURUSD", "BUY", 0.82, "trend")
    assert "EURUSD" in sent[0]
    assert "BUY" in sent[0]
    assert "82%" in sent[0]
    assert "trend" in sent[0]
