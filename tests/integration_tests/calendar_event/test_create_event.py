import uuid
from datetime import date

from cloud.dependencies.clients import resolve_calendar_event_client
from sebastian.domain.calendar import Calendars
from sebastian.domain.date_filter import DateFilter


def test_create_event_with_description():
    # Arrange
    client = resolve_calendar_event_client()
    unique_suffix = uuid.uuid4().hex[:8]
    test_title = f"[CREATE TEST] integration test create_event with description [{unique_suffix}]"
    test_date = date(2026, 4, 15)
    test_description = "book_id: 123456789\ntitle: Some Book\nlocation: Shelf A"
    event_id: str | None = None

    try:
        # Act
        client.create_event(
            Calendars.Primary, test_title, test_date, description=test_description
        )

        # Assert
        date_filter = DateFilter.from_dates(start=test_date)
        events = client.get_events(
            Calendars.Primary, q=test_title, date_filter=date_filter
        )
        assert len(events) == 1
        event = events[0]
        event_id = event.id
        assert event.description is not None
        assert "book_id: 123456789" in event.description
        assert "title: Some Book" in event.description
        assert "location: Shelf A" in event.description
    finally:
        if event_id is not None:
            client.delete_event(Calendars.Primary, event_id)
