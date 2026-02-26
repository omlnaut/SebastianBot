from pydantic import BaseModel

from cloud.helper.event_grid import EventGridMixin
from sebastian.protocols.models import SendMessage


class SendTelegramMessageEventGrid(EventGridMixin, BaseModel):
    message: str

    @staticmethod
    def from_application(app_event: SendMessage):
        return SendTelegramMessageEventGrid(
            message=app_event.message,
        )
