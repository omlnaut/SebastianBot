import logging

import telegram

from cloud.functions.infrastructure.telegram.config import (
    TelegramChat,
    TelegramConfig,
    TelegramToken,
)


class TelegramClient:
    def __init__(self, config: TelegramConfig):
        self.config = config
        # Hardcode Sebastian token and MainChat for now
        token = config.tokens[TelegramToken.Sebastian].token
        self.chat_id = config.chats[TelegramChat.MainChat].id
        self.bot = telegram.Bot(token)

    async def send_message(self, message: str) -> None:
        """Send a message to the configured chat."""
        logging.info(f"Sending Telegram message to chat_id {self.chat_id}")

        async with self.bot:
            await self.bot.send_message(chat_id=self.chat_id, text=message)

        logging.info("Telegram message sent successfully")
