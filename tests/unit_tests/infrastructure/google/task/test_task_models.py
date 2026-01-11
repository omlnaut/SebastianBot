from datetime import datetime
import json

import pytest
from cloud.functions.infrastructure.google.task.models import CreateTaskEvent
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
    assert result.subject == "create_task"
    assert result.event_type == "create_task_event"
    assert result.event_time is not None
    assert result.event_time >= test_start
    assert result.data_version == "1.0"
    # ID should be a valid UUID
    assert len(result.id) == 36


def test_to_output_with_minimal_fields(test_start: datetime):
    """Test to_output with only required fields."""
    event = CreateTaskEvent(title="Test Task")
    result = event.to_output()

    _assert_base_fields(result, test_start)
    data = result.get_json()
    assert data["title"] == "Test Task"
    assert data["notes"] is None
    assert data["due"] is None
    assert data["task_list_id"] == TaskListIds.Default.value


def test_to_output_with_all_fields(test_start: datetime):
    """Test to_output with all fields populated."""
    event = CreateTaskEvent(
        title="Test Task",
        notes="Test notes",
        due=datetime(2026, 1, 20, 10, 30),
        task_list_id=TaskListIds.Mangas,
    )
    result = event.to_output()

    assert isinstance(result, func.EventGridOutputEvent)
    assert result.subject == "create_task"
    assert result.event_type == "create_task_event"
    assert result.event_time is not None
    assert result.event_time >= test_start
    assert result.data_version == "1.0"
    assert len(result.id) == 36

    data = result.get_json()
    assert data["title"] == "Test Task"
    assert data["notes"] == "Test notes"
    assert data["due"] == "2026-01-20T10:30:00"  # ISO format from mode='json'
    assert data["task_list_id"] == TaskListIds.Mangas.value


def test_to_output_with_different_task_lists(test_start: datetime):
    """Test to_output with different task list IDs."""
    for task_list_id in TaskListIds:
        event = CreateTaskEvent(title="Test", task_list_id=task_list_id)
        result = event.to_output()

        _assert_base_fields(result, test_start)
        data = result.get_json()
        assert data["task_list_id"] == task_list_id.value


def test_to_output_data_is_model_dump(test_start: datetime):
    """Test that the data field correctly contains the model dump."""
    event = CreateTaskEvent(
        title="Test Task",
        notes="Test notes",
        due=datetime(2026, 1, 20, 10, 30),
        task_list_id=TaskListIds.Mangas,
    )
    result = event.to_output()
    expected_data = event.model_dump(mode="json")

    _assert_base_fields(result, test_start)
    assert result.get_json() == expected_data


def test_event_is_json_serializable(test_start: datetime):
    """Test that the event output can be serialized to JSON."""
    event = CreateTaskEvent(
        title="Test Task",
        notes="Test notes",
        due=datetime(2026, 1, 20, 10, 30),
        task_list_id=TaskListIds.Mangas,
    )
    result = event.to_output()

    # This will raise TypeError if any field is not JSON serializable
    json_string = json.dumps(result.get_json())
    assert json_string is not None

    # Verify we can deserialize it back and fields are correctly serialized
    parsed = json.loads(json_string)
    assert isinstance(parsed["task_list_id"], str)
    assert parsed["task_list_id"] == TaskListIds.Mangas.value
    assert isinstance(parsed["due"], str)
    assert parsed["due"] == "2026-01-20T10:30:00"


def test_unique_event_ids():
    """Test that each to_output call generates a unique ID."""
    event = CreateTaskEvent(title="Test Task")
    result1 = event.to_output()
    result2 = event.to_output()

    assert result1.id != result2.id
