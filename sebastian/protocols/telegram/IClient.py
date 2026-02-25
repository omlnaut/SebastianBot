from typing import Protocol


class ITelegramClient(Protocol):
    async def send_message(self, message: str) -> None:
        """Send a message to the configured Telegram chat."""
