from datetime import datetime

import pytest
from cloud.functions.infrastructure.AllHandler.models import AllHandlerEvent
from cloud.functions.infrastructure.google.task.models import CreateTaskEvent
from cloud.functions.infrastructure.telegram.models import SendTelegramMessageEvent
import azure.functions as func


@pytest.fixture
def test_start() -> datetime:
    """Fixture providing the test start time."""
    return datetime.now()


def _assert_base_fields(
    result: func.EventGridOutputEvent, test_start: datetime
) -> None:
    """Assert common fields for all EventGridOutputEvent results."""
    assert isinstance(result, func.EventGridOutputEvent)
    assert result.id == "allhandler-event"
    assert result.subject == "allhandler_event"
    assert result.event_type == "allhandler_event"
    assert result.event_time is not None
    assert result.event_time >= test_start
    assert result.data_version == "1.0"


def test_to_output_with_empty_events(test_start: datetime):
    """Test to_output with no events."""
    event = AllHandlerEvent()
    result = event.to_output()

    _assert_base_fields(result, test_start)
    assert result.get_json() == {
        "create_task_events": [],
        "send_telegram_message_events": [],
    }


def test_to_output_with_task_events(test_start: datetime):
    """Test to_output with create task events."""
    task_event = CreateTaskEvent(
        title="Test Task", notes="Test notes", due=datetime(2026, 1, 20)
    )
    event = AllHandlerEvent(create_task_events=[task_event])
    result = event.to_output()

    _assert_base_fields(result, test_start)
    assert len(result.get_json()["create_task_events"]) == 1

    task_event_data = result.get_json()["create_task_events"][0]
    assert task_event_data["title"] == "Test Task"
    assert task_event_data["notes"] == "Test notes"
    assert task_event_data["due"] == datetime(2026, 1, 20)
    assert result.get_json()["send_telegram_message_events"] == []


def test_to_output_with_telegram_events(test_start: datetime):
    """Test to_output with send telegram message events."""
    telegram_event = SendTelegramMessageEvent(message="Test message")
    event = AllHandlerEvent(send_telegram_message_events=[telegram_event])
    result = event.to_output()

    _assert_base_fields(result, test_start)
    assert result.get_json()["create_task_events"] == []
    assert len(result.get_json()["send_telegram_message_events"]) == 1
    telegram_event = result.get_json()["send_telegram_message_events"][0]
    assert telegram_event["message"] == "Test message"


def test_to_output_with_multiple_events(test_start: datetime):
    """Test to_output with both task and telegram events."""
    task_event1 = CreateTaskEvent(
        title="Task 1", notes="Notes 1", due=datetime(2026, 1, 20)
    )
    task_event2 = CreateTaskEvent(
        title="Task 2", notes="Notes 2", due=datetime(2026, 1, 21)
    )
    telegram_event1 = SendTelegramMessageEvent(message="Message 1")
    telegram_event2 = SendTelegramMessageEvent(message="Message 2")

    event = AllHandlerEvent(
        create_task_events=[task_event1, task_event2],
        send_telegram_message_events=[telegram_event1, telegram_event2],
    )
    result = event.to_output()

    _assert_base_fields(result, test_start)
    assert len(result.get_json()["create_task_events"]) == 2
    assert len(result.get_json()["send_telegram_message_events"]) == 2


def test_to_output_data_is_model_dump(test_start: datetime):
    """Test that the data field correctly contains the model dump."""
    task_event = CreateTaskEvent(title="Test", notes="Notes", due=datetime(2026, 1, 20))
    telegram_event = SendTelegramMessageEvent(message="Text")
    event = AllHandlerEvent(
        create_task_events=[task_event],
        send_telegram_message_events=[telegram_event],
    )

    result = event.to_output()
    expected_data = event.model_dump()

    _assert_base_fields(result, test_start)
    assert result.get_json() == expected_data
