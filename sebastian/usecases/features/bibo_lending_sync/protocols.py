from typing import Protocol

from pydantic import BaseModel, Field

from sebastian.domain.calendar import CalendarEvent, Calendars
from sebastian.domain.date_filter import DateFilter
from sebastian.usecases.shared.dates import TimeRange

__all__ = ["BiboClient", "CalendarClient"]


class BookLendingInfo(BaseModel):
    title: str = Field(min_length=1)
    id: str = Field(min_length=9, max_length=9)
    location: str = Field(min_length=1)
    lending_timerange: TimeRange


class BiboClient(Protocol):
    def fetch_open_lendings(self) -> list[BookLendingInfo]: ...


class CalendarClient(Protocol):
    def get_events(
        self,
        calendar: Calendars,
        date_filter: DateFilter | None = None,
        q: str | None = None,
    ) -> list[CalendarEvent]: ...
