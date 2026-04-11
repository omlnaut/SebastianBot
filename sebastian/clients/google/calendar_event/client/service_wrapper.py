# pyright: standard
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from sebastian.domain.calendar import CalendarEvent

from ._models import CalendarEventResponse, CalendarListEntry, EventDateTime


def _to_datetime(value: EventDateTime | None) -> datetime | None:
    if value is None:
        return None
    if value.dateTime:
        return datetime.fromisoformat(value.dateTime)
    if value.date:
        tz = ZoneInfo(value.timeZone) if value.timeZone else timezone.utc
        return datetime.fromisoformat(value.date).replace(tzinfo=tz)
    return None


def _to_rfc3339(value: datetime | date) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    return datetime(value.year, value.month, value.day, tzinfo=timezone.utc).isoformat()


def _to_domain(event: CalendarEventResponse) -> CalendarEvent:
    return CalendarEvent(
        id=event.id,
        title=event.summary,
        description=event.description,
        start=_to_datetime(event.start),
        end=_to_datetime(event.end),
    )


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

    def list_events(
        self,
        calendar_id: str,
        time_min: datetime | date | None = None,
        time_max: datetime | date | None = None,
        q: str | None = None,
    ) -> list[CalendarEvent]:
        kwargs: dict[str, object] = {
            "calendarId": calendar_id,
            "singleEvents": True,
            "orderBy": "startTime",
        }
        if time_min is not None:
            kwargs["timeMin"] = _to_rfc3339(time_min)
        if time_max is not None:
            kwargs["timeMax"] = _to_rfc3339(time_max)
        if q is not None:
            kwargs["q"] = q
        response = self._service.events().list(**kwargs).execute()
        event_responses = [
            CalendarEventResponse.model_validate(item)
            for item in response.get("items", [])
        ]
        return [_to_domain(event) for event in event_responses]

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
