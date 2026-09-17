from src import telegram_polling


def test_bot_telegram_polling_can_be_disabled_without_secrets(monkeypatch):
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)
    bot = telegram_polling.TelegramPollingBot()
    assert not bot.configured
    assert bot.poll_once() == 0
