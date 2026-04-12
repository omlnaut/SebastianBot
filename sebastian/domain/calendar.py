from datetime import datetime
from enum import Enum, auto

from pydantic import BaseModel, EmailStr, Field


class Calendar(BaseModel):
    id: EmailStr
    title: str = Field(min_length=1)


class CalendarEvent(BaseModel):
    id: str
    title: str | None = None
    description: str | None = None
    start: datetime
    end: datetime


class Calendars(Enum):
    Primary = auto()
    SharedPrimary = auto()
