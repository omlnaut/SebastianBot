# pyright: standard
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from ._models import CalendarListEntry


class CalendarServiceWrapper:
    def __init__(self, credentials: Credentials):
        self._service = build(
            "calendar", "v3", credentials=credentials, cache_discovery=False
        )

    def get_calendars(self) -> list[CalendarListEntry]:
        response = self._service.calendarList().list().execute()
        # from json?
        return [CalendarListEntry(**item) for item in response.get("items", [])]
