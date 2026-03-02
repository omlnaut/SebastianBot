from typing import Self

from cloud.helper.event_grid import EventGridModel
from sebastian.protocols.models import SendMessage


class SendTelegramMessageEventGrid(EventGridModel[SendMessage]):
    message: str

    @classmethod
    def from_application(cls, app_event: SendMessage) -> Self:
        return cls(
            message=app_event.message,
        )
