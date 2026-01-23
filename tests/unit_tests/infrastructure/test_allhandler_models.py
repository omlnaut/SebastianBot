from datetime import datetime
import json

import pytest
from cloud.functions.infrastructure.AllHandler.models import AllHandlerEventGrid
from cloud.functions.infrastructure.google.task.models import CreateTaskEventGrid
from cloud.functions.infrastructure.telegram.models import SendTelegramMessageEventGrid
import azure.functions as func

from sebastian.protocols.google_task.models import TaskListIds


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
    event = AllHandlerEventGrid()
    result = event.to_output()

    _assert_base_fields(result, test_start)
    assert result.get_json() == {
        "create_task_events": [],
        "archive_email_events": [],
        "put_email_in_to_read_events": [],
    }


def test_to_output_with_task_events(test_start: datetime):
    """Test to_output with create task events."""
    task_event = CreateTaskEventGrid(
        title="Test Task", notes="Test notes", due=datetime(2026, 1, 20)
    )
    event = AllHandlerEventGrid(create_task_events=[task_event])
    result = event.to_output()

    _assert_base_fields(result, test_start)
    assert len(result.get_json()["create_task_events"]) == 1

    task_event_data = result.get_json()["create_task_events"][0]
    assert task_event_data["title"] == "Test Task"
    assert task_event_data["notes"] == "Test notes"
    assert (
        task_event_data["due"] == "2026-01-20T00:00:00"
    )  # ISO format from mode='json'
    assert task_event_data["task_list_id"] == TaskListIds.Default.value


def test_to_output_with_multiple_events(test_start: datetime):
    """Test to_output with both task and telegram events."""
    task_event1 = CreateTaskEventGrid(
        title="Task 1", notes="Notes 1", due=datetime(2026, 1, 20)
    )
    task_event2 = CreateTaskEventGrid(
        title="Task 2", notes="Notes 2", due=datetime(2026, 1, 21)
    )

    event = AllHandlerEventGrid(
        create_task_events=[task_event1, task_event2],
    )
    result = event.to_output()

    _assert_base_fields(result, test_start)
    assert len(result.get_json()["create_task_events"]) == 2


def test_event_is_json_serializable():
    """Test that the event output can be serialized to JSON."""
    task_event = CreateTaskEventGrid(
        title="Test Task", notes="Test notes", due=datetime(2026, 1, 20)
    )
    event = AllHandlerEventGrid(
        create_task_events=[task_event],
    )

    result = event.to_output()

    # This will raise TypeError if any field is not JSON serializable
    json_string = json.dumps(result.get_json())
    assert json_string is not None

    # Verify we can deserialize it back
    parsed = json.loads(json_string)
    assert parsed["create_task_events"][0]["task_list_id"] == TaskListIds.Default.value
