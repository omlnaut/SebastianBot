from cloud.helper.event_grid import EventGridModel
from sebastian.protocols.models import SendMessage


class SendTelegramMessageEventGrid(EventGridModel):
    message: str

    @staticmethod
    def from_application(app_event: SendMessage):
        return SendTelegramMessageEventGrid(
            message=app_event.message,
        )

    def to_application(self) -> SendMessage:
        return SendMessage(message=self.message)
