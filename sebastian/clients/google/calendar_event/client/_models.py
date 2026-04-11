from pydantic import BaseModel, ConfigDict, EmailStr, Field


class CalendarListEntry(BaseModel):
    id: EmailStr
    summary: str = Field(min_length=1)


class EventDateTime(BaseModel):
    dateTime: str | None = None
    timeZone: str | None = None
    date: str | None = None

    model_config = ConfigDict(extra="allow")


class CalendarEventResponse(BaseModel):
    id: str
    summary: str | None = None
    description: str | None = None
    start: EventDateTime | None = None
    end: EventDateTime | None = None

    model_config = ConfigDict(extra="allow")
