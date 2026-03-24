from pydantic import BaseModel, EmailStr, Field


class CalendarListEntry(BaseModel):
    id: EmailStr
    summary: str = Field(min_length=1)
