from typing import Self, override

from cloud.helper.event_grid import EventGridModel
from sebastian.domain.calendar import Calendars
from sebastian.domain.side_effects import DeleteCalendarEvent


class DeleteCalendarEventEventGrid(EventGridModel[DeleteCalendarEvent]):
    calendar: Calendars
    event_id: str

    @classmethod
    @override
    def from_application(cls, app_event: DeleteCalendarEvent) -> Self:
        return cls(
            calendar=app_event.calendar,
            event_id=app_event.event_id,
        )
