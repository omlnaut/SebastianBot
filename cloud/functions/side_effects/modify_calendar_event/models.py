from datetime import date
from typing import Self, override

from cloud.helper.event_grid import EventGridModel
from sebastian.domain.calendar import Calendars
from sebastian.domain.side_effects import ModifyCalendarEvent


class ModifyCalendarEventEventGrid(EventGridModel[ModifyCalendarEvent]):
    calendar: Calendars
    event_id: str
    date: date

    @classmethod
    @override
    def from_application(cls, app_event: ModifyCalendarEvent) -> Self:
        return cls(
            calendar=app_event.calendar,
            event_id=app_event.event_id,
            date=app_event.date,
        )
