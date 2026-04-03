import logging
from dataclasses import dataclass
from typing import Protocol, Sequence

from sebastian.protocols.models import BaseActorEvent
from sebastian.usecases.usecase_handler import UseCaseHandler


@dataclass
class Request:
    message: str


class TelegramClient(Protocol):
    def send_message(self, message: str) -> None:
        """Should send a telegram message"""
        ...


class Handler(UseCaseHandler[Request]):
    def __init__(self, telegram_client: TelegramClient):
        self._client = telegram_client

    def handle(self, request: Request) -> Sequence[BaseActorEvent]:
        logging.info(f"Start to send telegram message: {request.message}")
        self._client.send_message(request.message)
        logging.info(f"Finished sending telegram message: {request.message}")

        return []
