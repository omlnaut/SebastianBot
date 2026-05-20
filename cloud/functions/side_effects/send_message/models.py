from typing import Self, override

from cloud.helper.event_grid import EventGridModel
from sebastian.domain.side_effect import SendMessage


class SendTelegramMessageEventGrid(EventGridModel[SendMessage]):
    message: str

    @classmethod
    @override
    def from_application(cls, app_event: SendMessage) -> Self:
        return cls(
            message=app_event.message,
        )
