from google.oauth2.credentials import Credentials

from sebastian.domain.calendar import Calendar
from .service_wrapper import CalendarServiceWrapper


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
