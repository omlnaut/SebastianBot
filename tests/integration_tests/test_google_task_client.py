import pytest
from datetime import datetime, timedelta, timezone

from cloud.dependencies.clients import resolve_google_task_client
from sebastian.protocols.google_task.models import TaskListIds


@pytest.fixture
def google_task_client():
    return resolve_google_task_client()


def test_google_task_client_integration(google_task_client):
    title = f"Integration Test Task {datetime.now().isoformat()}"
    notes = "This is a test task created by the integration test."
    due_date = datetime.now(timezone.utc) + timedelta(days=1)

    def create_task():
        created_task = google_task_client.create_task_with_notes(
            tasklist_id=TaskListIds.Default, title=title, notes=notes, due_date=due_date
        )

        assert created_task.title == title
        assert created_task.notes == notes
        return created_task

    def fetch_task_id() -> str:
        tasks_result = google_task_client.get_tasks(tasklist_id=TaskListIds.Default)
        assert not tasks_result.has_errors()

        tasks = tasks_result.item
        assert tasks is not None

        found_task = next((t for t in tasks if t.title == title), None)
        assert (
            found_task is not None
        ), f"Task with title '{title}' not found in task list."

        return found_task.id

    def set_task_as_completed(task_id: str):
        complete_result = google_task_client.set_task_to_completed(
            tasklist_id=TaskListIds.Default, task_id=task_id
        )
        assert not complete_result.has_errors()

    def check_task_is_completed(task_id: str):
        tasks_result = google_task_client.get_tasks(tasklist_id=TaskListIds.Default)
        assert not tasks_result.has_errors()

        tasks = tasks_result.item
        assert tasks is not None

        found_task = next((t for t in tasks if t.id == task_id), None)
        assert (
            found_task is None
        ), f"Task with ID '{task_id}' should not be returned after being marked completed."

    create_task()
    task_id = fetch_task_id()
    set_task_as_completed(task_id)
    check_task_is_completed(task_id)
