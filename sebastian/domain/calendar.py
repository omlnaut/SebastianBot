from enum import Enum, auto

from pydantic import BaseModel, EmailStr, Field


class Calendar(BaseModel):
    id: EmailStr
    title: str = Field(min_length=1)


class Calendars(Enum):
    MyDefault = auto()
