from datetime import datetime, timezone

from sebastian.clients.google.task.client.create_task_with_notes import build_task_body

from pydantic import RootModel, AwareDatetime


def validate_with_pydantic(timestamp_str: str):
    RootModel[AwareDatetime](timestamp_str)  # type: ignore


def test_build_task_body_due_is_rfc3339_naive():
    body = build_task_body("title", "notes", datetime(2026, 5, 4))
    validate_with_pydantic(body["due"])


def test_build_task_body_due_is_rfc3339_aware():
    body = build_task_body("title", "notes", datetime(2026, 5, 4, tzinfo=timezone.utc))
    validate_with_pydantic(body["due"])
