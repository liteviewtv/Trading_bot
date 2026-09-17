from src.telegram_polling import TelegramPollingBot


def test_poll_once_routes_authorized_command(monkeypatch):
    bot = TelegramPollingBot(token="token", chat_id="123", timeout=1)
    sent = []
    bot.notifier.send = lambda message: sent.append(message) or True
    bot._request = lambda method, params: [{"update_id": 10, "message": {"chat": {"id": 123}, "text": "/help"}}]
    assert bot.poll_once() == 1
    assert "/pause" in sent[0]


def test_poll_once_ignores_other_chat(monkeypatch):
    bot = TelegramPollingBot(token="token", chat_id="123", timeout=1)
    sent = []
    bot.notifier.send = lambda message: sent.append(message) or True
    bot._request = lambda method, params: [{"update_id": 10, "message": {"chat": {"id": 999}, "text": "/help"}}]
    assert bot.poll_once() == 1
    assert sent == []
