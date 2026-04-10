from datetime import date
from typing import Self, override

from cloud.helper.event_grid import EventGridModel
from sebastian.domain.calendar import Calendars
from sebastian.protocols.models import CreateCalendarEvent


class CreateCalendarEventEventGrid(EventGridModel[CreateCalendarEvent]):
    calendar: Calendars
    title: str
    date: date

    @classmethod
    @override
    def from_application(cls, app_event: CreateCalendarEvent) -> Self:
        return cls(
            calendar=app_event.calendar,
            title=app_event.title,
            date=app_event.date,
        )
