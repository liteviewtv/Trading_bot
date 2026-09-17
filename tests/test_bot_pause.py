from src import telegram_polling


def test_runner_telegram_pause_state_is_available(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "123")
    bot = telegram_polling.TelegramPollingBot()
    bot.control.paused = True
    assert bot.control.paused is True
