# pyright: standard
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from sebastian.domain.calendar import CalendarEvent
from sebastian.domain.shared import DateFilter

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


def _to_rfc3339(value: datetime) -> str:
    return value.isoformat()


def _to_domain(event: CalendarEventResponse) -> CalendarEvent | None:
    start = _to_datetime(event.start)
    end = _to_datetime(event.end)
    if start is None or end is None:
        return None
    return CalendarEvent(
        id=event.id,
        title=event.summary,
        description=event.description,
        start=start,
        end=end,
    )


class CalendarServiceWrapper:
    def __init__(self, credentials: Credentials):
        self._service = build(
            "calendar", "v3", credentials=credentials, cache_discovery=False
        )

    def get_calendars(self) -> list[CalendarListEntry]:
        response = self._service.calendarList().list().execute()
        return [
            CalendarListEntry.model_validate(item) for item in response.get("items", [])
        ]

    def list_events(
        self,
        calendar_id: str,
        date_filter: DateFilter | None = None,
        q: str | None = None,
    ) -> list[CalendarEvent]:
        kwargs: dict[str, object] = {
            "calendarId": calendar_id,
            "singleEvents": True,
        }
        if date_filter is not None:
            if date_filter.start is not None:
                kwargs["timeMin"] = _to_rfc3339(date_filter.start)
                kwargs["orderBy"] = "startTime"
            if date_filter.end is not None:
                kwargs["timeMax"] = _to_rfc3339(date_filter.end)
        if q is not None:
            kwargs["q"] = q
        response = self._service.events().list(**kwargs).execute()
        event_responses = [
            CalendarEventResponse.model_validate(item)
            for item in response.get("items", [])
        ]
        return [
            domain
            for event in event_responses
            if (domain := _to_domain(event)) is not None
        ]

    def create_event(
        self, calendar_id: str, title: str, date: date, description: str | None = None
    ) -> None:
        day_after = date + timedelta(days=1)
        event_body: dict[str, object] = {
            "summary": title,
            "start": {
                "date": date.strftime("%Y-%m-%d"),
            },
            "end": {
                "date": day_after.strftime("%Y-%m-%d"),
            },
        }
        if description is not None:
            event_body["description"] = description
        self._service.events().insert(calendarId=calendar_id, body=event_body).execute()

    def delete_event(self, calendar_id: str, event_id: str) -> None:
        self._service.events().delete(
            calendarId=calendar_id, eventId=event_id
        ).execute()

    def modify_event(self, calendar_id: str, event_id: str, date: date) -> None:
        day_after = date + timedelta(days=1)
        patch_body = {
            "start": {"date": date.strftime("%Y-%m-%d")},
            "end": {"date": day_after.strftime("%Y-%m-%d")},
        }
        self._service.events().patch(
            calendarId=calendar_id, eventId=event_id, body=patch_body
        ).execute()
