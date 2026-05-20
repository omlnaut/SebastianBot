from sebastian.domain.side_effect import CompleteTask
from sebastian.domain.task import Task, TaskLists
from sebastian.usecases.features.check_parcel_received.handler import Handler, Request


class _FakeTaskClient:
    def __init__(self, tasks: list[Task]):
        self._tasks = tasks

    def get_tasks(
        self,
        tasklist: TaskLists = TaskLists.Default,
        include_completed: bool = False,
    ) -> list[Task]:
        return [task for task in self._tasks if task.tasklist == tasklist]


class _FakeDhlClient:
    def __init__(self, retrieved: bool = False):
        self.retrieved = retrieved
        self.calls: list[str] = []

    def is_retrieved(self, tracking_number: str) -> bool:
        self.calls.append(tracking_number)
        return self.retrieved


def _task(task_id: str, notes: str) -> Task:
    return Task(
        id=task_id,
        tasklist=TaskLists.Default,
        title="Paket abholen",
        notes=notes,
    )


def test_check_parcel_received_completes_task_when_contract_note_is_retrieved():
    task = _task(
        "task-1",
        "Book\nAbholort: Packstation 123\nTracking: ab12cd34\nDELIVERY_READY",
    )
    dhl = _FakeDhlClient(retrieved=True)

    result = Handler(task_client=_FakeTaskClient([task]), dhl_client=dhl).handle(Request())

    assert result == [CompleteTask(tasklist=TaskLists.Default, task_id="task-1")]
    assert dhl.calls == ["AB12CD34"]


def test_check_parcel_received_skips_task_tag_without_tracking_number():
    task = _task("task-1", "Book\nAbholort: Packstation 123\nDELIVERY_READY")
    dhl = _FakeDhlClient(retrieved=True)

    result = Handler(task_client=_FakeTaskClient([task]), dhl_client=dhl).handle(Request())

    assert result == []
    assert dhl.calls == []


def test_check_parcel_received_malformed_notes_are_skipped_safely():
    task = _task("task-1", "Book Tracking: inline-value\nDELIVERY_READY")
    dhl = _FakeDhlClient(retrieved=True)

    result = Handler(task_client=_FakeTaskClient([task]), dhl_client=dhl).handle(Request())

    assert result == []
    assert dhl.calls == []
