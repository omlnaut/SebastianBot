from datetime import datetime
from zoneinfo import ZoneInfo

from sebastian.domain.side_effect import PatchTask
from sebastian.domain.task import Task, TaskLists
from sebastian.usecases.features.set_missing_task_due_date.handler import (
    Handler,
    Request,
)


class _FakeTaskClient:
    def __init__(self, tasks: list[Task]):
        self._tasks = tasks

    def get_tasks(
        self,
        tasklist: TaskLists = TaskLists.Default,
        include_completed: bool = False,
    ) -> list[Task]:
        return [task for task in self._tasks if task.tasklist == tasklist]


def _task(
    task_id: str, due: datetime | None, tasklist: TaskLists = TaskLists.Default
) -> Task:
    return Task(id=task_id, tasklist=tasklist, title="Mail", due=due)


def test_sets_today_for_tasks_without_due_date():
    today = datetime.now(ZoneInfo("Europe/Berlin")).date()
    client = _FakeTaskClient([_task("t1", None)])

    result = Handler(task_client=client).handle(Request())

    assert result == [
        PatchTask.SetDueDate(tasklist=TaskLists.Default, task_id="t1", due_date=today)
    ]


def test_ignores_tasks_with_due_date():
    client = _FakeTaskClient([_task("t1", datetime(2030, 1, 1))])

    assert Handler(task_client=client).handle(Request()) == []


def test_ignores_other_tasklists_by_default():
    client = _FakeTaskClient([_task("t1", None, TaskLists.Mangas)])

    assert Handler(task_client=client).handle(Request()) == []


def test_empty_task_list():
    assert Handler(task_client=_FakeTaskClient([])).handle(Request()) == []
