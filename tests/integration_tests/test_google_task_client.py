import pytest
from datetime import datetime, timedelta, timezone

from cloud.dependencies.clients import resolve_google_task_client
from sebastian.clients.google.task.client import GoogleTaskClient
from sebastian.domain.task import TaskLists
from tests.helper import first_or_none


@pytest.fixture
def google_task_client() -> GoogleTaskClient:
    return resolve_google_task_client()


def test_google_task_client_integration(google_task_client: GoogleTaskClient):
    title = f"Integration Test Task {datetime.now().isoformat()}"
    notes = "This is a test task created by the integration test."
    due_date = datetime.now(timezone.utc) + timedelta(days=1)

    def create_task():
        created_task = google_task_client.create_task_with_notes(
            tasklist=TaskLists.Default, title=title, notes=notes, due_date=due_date
        )

        assert created_task.title == title
        assert created_task.notes == notes
        return created_task

    def fetch_task_id() -> str:
        tasks = google_task_client.get_tasks(tasklist=TaskLists.Default)
        assert tasks is not None

        found_task = first_or_none(tasks, lambda t: t.title == title)
        assert (
            found_task is not None
        ), f"Task with title '{title}' not found in task list."

        return found_task.id

    def set_task_as_completed(task_id: str):
        google_task_client.set_task_to_completed(
            tasklist=TaskLists.Default, task_id=task_id
        )

    def check_task_is_completed(task_id: str):
        tasks = google_task_client.get_tasks(tasklist=TaskLists.Default)
        assert tasks is not None

        found_task = first_or_none(tasks, lambda t: t.id == task_id)
        assert (
            found_task is None
        ), f"Task with ID '{task_id}' should not be returned after being marked completed."

    create_task()
    task_id = fetch_task_id()
    set_task_as_completed(task_id)
    check_task_is_completed(task_id)
