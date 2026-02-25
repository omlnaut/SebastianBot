import logging

from sebastian.protocols.telegram.IClient import ITelegramClient


async def send_telegram_message(client: ITelegramClient, message: str) -> None:
    """Send a telegram message using the provided client.

    Args:
        client: TelegramClient instance with credentials
        message: Message text to send
    """
    logging.info("Sending telegram message via client")
    await client.send_message(message)
    logging.info("Telegram message sent successfully via service")
