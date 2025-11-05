import logging

import telegram


async def send_telegram_message(token: str, chat_id: int, message: str):
    logging.info(f"Sending Telegram message to chat_id {chat_id}")
    bot = telegram.Bot(token)

    async with bot:
        await bot.send_message(chat_id=chat_id, text=message)

    logging.info("Telegram message sent successfully")
