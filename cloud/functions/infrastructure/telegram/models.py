import azure.functions as func
from pydantic import BaseModel

from cloud.helper.event_grid_mixin import EventGridMixin

import datetime
import uuid


class SendTelegramMessageEventGrid(EventGridMixin, BaseModel):
    message: str
