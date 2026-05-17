from datetime import datetime, timezone
import re

import pytest

from cloud.dependencies.clients import resolve_google_task_client
from sebastian.clients.dhl.client import DhlClient
from sebastian.clients.google.task.client import GoogleTaskClient
from sebastian.domain.date_filter import DateFilter
from sebastian.domain.task import TaskLabels, TaskLists

_TRACKING_PATTERN = re.compile(r"Tracking:\s*([A-Z0-9]+)")


@pytest.fixture
def google_task_client() -> GoogleTaskClient:
    return resolve_google_task_client()


@pytest.fixture
def dhl_client() -> DhlClient:
    return DhlClient()


def _last_complete_month_range(
    now: datetime | None = None,
) -> tuple[datetime, datetime]:
    current = now or datetime.now(timezone.utc)
    first_of_current_month = datetime(
        current.year, current.month, 1, tzinfo=timezone.utc
    )

    if first_of_current_month.month == 1:
        previous_year = first_of_current_month.year - 1
        previous_month = 12
    else:
        previous_year = first_of_current_month.year
        previous_month = first_of_current_month.month - 1

    start = datetime(previous_year, previous_month, 1, tzinfo=timezone.utc)
    end = first_of_current_month
    return start, end


def _extract_tracking_id(notes: str | None) -> str | None:
    if notes is None:
        return None
    match = _TRACKING_PATTERN.search(notes)
    if match is None:
        return None
    return match.group(1)


def test_has_packstation_status_from_last_complete_month_delivery_ready_tasks(
    google_task_client: GoogleTaskClient,
    dhl_client: DhlClient,
):
    due_min, due_max = _last_complete_month_range()
    tasks = google_task_client.get_tasks(
        tasklist=TaskLists.Default,
        include_completed=True,
        due=DateFilter.range(start=due_min, end=due_max),
    )

    completed_delivery_ready_tasks = [
        task
        for task in tasks
        if task.notes is not None and TaskLabels.DeliveryReady.value in task.notes
    ]

    assert completed_delivery_ready_tasks, (
        "No completed DELIVERY_READY tasks found in the last complete month. "
        "Create/complete one task first to run this integration test."
    )

    target_task = completed_delivery_ready_tasks[0]
    tracking_id = _extract_tracking_id(target_task.notes)

    assert tracking_id is not None, (
        "No tracking number found in completed DELIVERY_READY tasks from the "
        "last complete month. Expected notes to include 'Tracking: <id>'."
    )
    assert dhl_client.is_retrieved(tracking_id) is True
