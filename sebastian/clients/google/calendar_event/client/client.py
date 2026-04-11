from datetime import date, datetime

from google.oauth2.credentials import Credentials

from sebastian.domain.calendar import Calendar, CalendarEvent, Calendars

from .service_wrapper import CalendarServiceWrapper


def to_id(calendar: Calendars) -> str:
    match calendar:
        case Calendars.Primary:
            return "oneironaut.oml@gmail.com"
        case _:
            raise ValueError(f"Unsupported calendar: {calendar}")


class CalendarEventClient:
    def __init__(self, credentials: Credentials):
        self._service = CalendarServiceWrapper(credentials)

    def get_calendars(self) -> list[Calendar]:
        """
        Fetches at most 100 calendars.
        Default value defined here: https://developers.google.com/workspace/calendar/api/v3/reference/calendarList/list
        """
        calendars = self._service.get_calendars()
        return [
            Calendar(id=calendar.id, title=calendar.summary) for calendar in calendars
        ]

    def get_events(
        self,
        calendar: Calendars,
        time_min: datetime | date | None = None,
        time_max: datetime | date | None = None,
        q: str | None = None,
    ) -> list[CalendarEvent]:
        calendar_id = to_id(calendar)
        return self._service.list_events(
            calendar_id, time_min=time_min, time_max=time_max, q=q
        )

    def create_event(self, calendar: Calendars, title: str, date: date) -> None:
        calendar_id = to_id(calendar)
        self._service.create_event(calendar_id, title, date)
