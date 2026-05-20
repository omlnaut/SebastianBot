from typing import Protocol

from sebastian.domain.bibo import Lending
from sebastian.domain.calendar import CalendarEvent, Calendars
from sebastian.domain.shared import DateFilter

__all__ = ["BiboClient", "CalendarClient"]


class BiboClient(Protocol):
    def fetch_open_lendings(self) -> list[Lending]: ...


class CalendarClient(Protocol):
    def get_events(
        self,
        calendar: Calendars,
        date_filter: DateFilter | None = None,
        q: str | None = None,
    ) -> list[CalendarEvent]: ...
