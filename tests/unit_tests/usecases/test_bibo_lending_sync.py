from datetime import datetime, timezone

from sebastian.domain.task import Task, TaskLists
from sebastian.protocols.models import BaseActorEvent, CompleteTask, CreateTask
from sebastian.shared.dates import TimeRange
from sebastian.usecases.features.bibo_lending_sync.handler import Handler, Request
from sebastian.usecases.features.bibo_lending_sync.protocols import BookLendingInfo

_TASKLIST = TaskLists.Bibo


def _make_lending(
    book_id: str = "123456789",
    title: str = "Some Book",
    location: str = "Shelf A",
    from_date: datetime = datetime(2026, 3, 1, tzinfo=timezone.utc),
    to_date: datetime = datetime(2026, 4, 1, tzinfo=timezone.utc),
) -> BookLendingInfo:
    return BookLendingInfo(
        title=title,
        id=book_id,
        location=location,
        lending_timerange=TimeRange(from_date=from_date, to_date=to_date),
    )


def _make_task(
    book_id: str | None = "123456789",
    due: datetime | None = datetime(2026, 4, 1, tzinfo=timezone.utc),
    task_id: str = "task-1",
) -> Task:
    notes = f"book_id: {book_id}\ntitle: Some Book" if book_id else None
    return Task(id=task_id, tasklist=_TASKLIST, title="bibo", due=due, notes=notes)


class _FakeBiboClient:
    def __init__(self, lendings: list[BookLendingInfo]):
        self._lendings = lendings

    def fetch_open_lendings(self) -> list[BookLendingInfo]:
        return self._lendings


class _FakeTaskClient:
    def __init__(self, tasks: list[Task]):
        self._tasks = tasks

    def get_tasks(self, tasklist: TaskLists) -> list[Task]:
        return self._tasks


def _run(lendings: list[BookLendingInfo], tasks: list[Task]) -> list[BaseActorEvent]:
    handler = Handler(
        bibo_client=_FakeBiboClient(lendings),
        task_client=_FakeTaskClient(tasks),
    )
    return handler.handle(Request())


def test_new_lending_creates_task():
    lending = _make_lending()

    result = _run(lendings=[lending], tasks=[])

    assert len([t for t in result if isinstance(t, CreateTask)]) == 1
    assert len([t for t in result if isinstance(t, CompleteTask)]) == 0
    task = [t for t in result if isinstance(t, CreateTask)][0]
    assert task.title == "Bibo: Some Book"
    assert task.tasklist == _TASKLIST
    assert task.due == lending.lending_timerange.to_date
    assert task.notes is not None
    assert "book_id: 123456789" in task.notes


def test_new_lending_notes_contain_all_fields():
    lending = _make_lending(
        book_id="987654321",
        title="Another Book",
        location="Floor 2",
        from_date=datetime(2026, 3, 5, tzinfo=timezone.utc),
        to_date=datetime(2026, 4, 10, tzinfo=timezone.utc),
    )

    result = _run(lendings=[lending], tasks=[])

    notes = [t for t in result if isinstance(t, CreateTask)][0].notes
    assert notes is not None
    assert "book_id: 987654321" in notes
    assert "title: Another Book" in notes
    assert "location: Floor 2" in notes
    assert "from: 2026-03-05" in notes
    assert "to: 2026-04-10" in notes


def test_existing_task_same_due_no_action():
    due = datetime(2026, 4, 1, tzinfo=timezone.utc)
    lending = _make_lending(to_date=due)
    task = _make_task(due=due)

    result = _run(lendings=[lending], tasks=[task])

    assert [t for t in result if isinstance(t, CreateTask)] == []
    assert [t for t in result if isinstance(t, CompleteTask)] == []


def test_due_date_changed_completes_and_recreates():
    old_due = datetime(2026, 3, 20, tzinfo=timezone.utc)
    new_due = datetime(2026, 4, 5, tzinfo=timezone.utc)
    lending = _make_lending(to_date=new_due)
    task = _make_task(due=old_due, task_id="task-old")

    result = _run(lendings=[lending], tasks=[task])

    assert len([t for t in result if isinstance(t, CompleteTask)]) == 1
    assert [t for t in result if isinstance(t, CompleteTask)][0] == CompleteTask(
        tasklist=_TASKLIST, task_id="task-old"
    )
    assert len([t for t in result if isinstance(t, CreateTask)]) == 1
    assert [t for t in result if isinstance(t, CreateTask)][0].due == new_due


def test_task_with_no_due_date_treated_as_changed():
    lending = _make_lending(to_date=datetime(2026, 4, 1, tzinfo=timezone.utc))
    task = _make_task(task_id="task-noduedate", due=None)

    result = _run(lendings=[lending], tasks=[task])

    assert len([t for t in result if isinstance(t, CompleteTask)]) == 1
    assert [t for t in result if isinstance(t, CompleteTask)][0].task_id == "task-noduedate"
    assert len([t for t in result if isinstance(t, CreateTask)]) == 1


def test_returned_book_task_is_completed():
    task = _make_task(task_id="task-returned", book_id="123456789")

    result = _run(lendings=[], tasks=[task])

    assert len([t for t in result if isinstance(t, CompleteTask)]) == 1
    assert [t for t in result if isinstance(t, CompleteTask)][0] == CompleteTask(
        tasklist=_TASKLIST, task_id="task-returned"
    )
    assert [t for t in result if isinstance(t, CreateTask)] == []


def test_task_without_book_id_is_ignored():
    task = _make_task(task_id="task-noid", book_id=None)

    result = _run(lendings=[], tasks=[task])

    assert [t for t in result if isinstance(t, CompleteTask)] == []
    assert [t for t in result if isinstance(t, CreateTask)] == []


def test_no_lendings_no_tasks_returns_empty():
    result = _run(lendings=[], tasks=[])

    assert result == []


def test_mixed_scenario():
    unchanged_due = datetime(2026, 4, 1, tzinfo=timezone.utc)
    changed_old_due = datetime(2026, 3, 10, tzinfo=timezone.utc)
    changed_new_due = datetime(2026, 4, 15, tzinfo=timezone.utc)

    lending_new = _make_lending(book_id="111111111", title="New Book")
    lending_unchanged = _make_lending(
        book_id="222222222", title="Unchanged Book", to_date=unchanged_due
    )
    lending_changed = _make_lending(
        book_id="333333333", title="Changed Book", to_date=changed_new_due
    )

    task_unchanged = _make_task(
        task_id="task-unchanged", book_id="222222222", due=unchanged_due
    )
    task_changed = _make_task(
        task_id="task-changed", book_id="333333333", due=changed_old_due
    )
    task_returned = _make_task(
        task_id="task-returned", book_id="444444444", due=unchanged_due
    )

    result = _run(
        lendings=[lending_new, lending_unchanged, lending_changed],
        tasks=[task_unchanged, task_changed, task_returned],
    )

    created_ids = {t.title for t in [t for t in result if isinstance(t, CreateTask)]}
    assert "Bibo: New Book" in created_ids
    assert "Bibo: Changed Book" in created_ids
    assert "Bibo: Unchanged Book" not in created_ids
    assert len([t for t in result if isinstance(t, CreateTask)]) == 2

    completed_ids = {t.task_id for t in [t for t in result if isinstance(t, CompleteTask)]}
    assert "task-changed" in completed_ids
    assert "task-returned" in completed_ids
    assert "task-unchanged" not in completed_ids
    assert len([t for t in result if isinstance(t, CompleteTask)]) == 2
