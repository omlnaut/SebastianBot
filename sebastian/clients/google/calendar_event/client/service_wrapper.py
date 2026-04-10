# pyright: standard
from datetime import date, timedelta

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
        return [
            CalendarListEntry.model_validate(item) for item in response.get("items", [])
        ]

    def create_event(self, calendar_id: str, title: str, date: date) -> None:
        day_after = date + timedelta(days=1)
        event_body = {
            "summary": title,
            "start": {
                "date": date.strftime("%Y-%m-%d"),
            },
            "end": {
                "date": day_after.strftime("%Y-%m-%d"),
            },
        }
        self._service.events().insert(calendarId=calendar_id, body=event_body).execute()
