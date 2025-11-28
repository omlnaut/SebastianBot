import logging

import telegram

from sebastian.clients.telegram.config import TelegramConfig


class TelegramClient:
    def __init__(self, config: TelegramConfig):
        self._chat_id = config.chat_id
        self._bot = telegram.Bot(config.token)

    async def send_message(self, message: str) -> None:
        """Send a message to the configured chat."""
        logging.info(f"Sending Telegram message to chat_id {self._chat_id}")

        async with self._bot:
            await self._bot.send_message(chat_id=self._chat_id, text=message)

        logging.info("Telegram message sent successfully")
