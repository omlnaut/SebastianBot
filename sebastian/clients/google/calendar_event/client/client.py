from datetime import datetime

from google.oauth2.credentials import Credentials

from sebastian.domain.calendar import Calendar, Calendars

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

    def create_event(self, calendar: Calendars, title: str, date: date) -> None:
        calendar_id = to_id(calendar)
        self._service.create_event(calendar_id, title, date)
