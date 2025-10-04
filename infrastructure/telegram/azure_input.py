from shared.secrets import get_secret


def load_telegram_token() -> str:
    return get_secret("TelegramBotToken")
