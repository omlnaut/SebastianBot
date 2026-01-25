from pydantic import BaseModel

from cloud.helper.EventGridMixin import EventGridMixin


class SendTelegramMessageEventGrid(EventGridMixin, BaseModel):
    message: str
