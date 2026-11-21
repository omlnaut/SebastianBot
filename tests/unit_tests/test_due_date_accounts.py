from datetime import datetime, timezone
from unittest.mock import Mock

import azure.functions as func
import pytest

import function_app  # noqa: F401
from cloud.dependencies import usecases
from cloud.functions.features import set_missing_task_due_date_function as timer
from cloud.functions.side_effects import shared
from cloud.functions.side_effects.complete_task import function as complete
from cloud.functions.side_effects.send_message.models import SendTelegramMessageEventGrid
from sebastian.domain.task import GoogleTaskAccount, Task, TaskLists
from sebastian.usecases.features.set_missing_task_due_date import Handler


def _event(data: dict[str, object]) -> func.EventGridEvent:
    return func.EventGridEvent(
        id="event",
        data=data,
        topic="test",
        subject="CompleteTask",
        event_type="CompleteTask_event",
        event_time=datetime.now(timezone.utc),
        data_version="1.0",
    )


def test_both_accounts_generate_and_route_updates(monkeypatch):
    task_clients = {}
    for account in GoogleTaskAccount:
        client = Mock()
        client.get_tasks.return_value = [
            Task(id="same-id", tasklist=TaskLists.Default, title=account.value)
        ]
        task_clients[account] = client

    sent = []
    monkeypatch.setattr(
        timer,
        "resolve_set_missing_task_due_date",
        lambda account: Handler(task_clients[account]),
    )
    monkeypatch.setattr(timer, "send_eventgrid_events", lambda events: sent.extend(events))
    monkeypatch.setattr(
        usecases,
        "resolve_complete_task",
        lambda account=GoogleTaskAccount.Original: usecases.complete_task.Handler(
            task_clients[account]
        ),
    )
    monkeypatch.setattr(shared, "send_eventgrid_events", lambda events: sent.extend(events))

    timer.set_missing_task_due_date.build().get_user_function()(None)
    assert [event.account for event in sent] == list(GoogleTaskAccount)

    for event in list(sent):
        complete.complete_task.build().get_user_function()(
            _event(event.model_dump(mode="json"))
        )

    for account, client in task_clients.items():
        client.patch_task.assert_called_once()
        assert client.patch_task.call_args.args == (TaskLists.Default, "same-id")
        assert client.patch_task.call_args.kwargs["due_date"] is not None


@pytest.mark.parametrize("failed", list(GoogleTaskAccount))
def test_account_failure_does_not_stop_the_other(monkeypatch, failed):
    processed = []
    sent = []

    def resolve(account):
        if account == failed:
            raise RuntimeError("sensitive-token")
        client = Mock()
        client.get_tasks.return_value = []
        processed.append(account)
        return Handler(client)

    monkeypatch.setattr(timer, "resolve_set_missing_task_due_date", resolve)
    monkeypatch.setattr(timer, "send_eventgrid_events", lambda events: sent.extend(events))

    timer.set_missing_task_due_date.build().get_user_function()(None)

    assert processed == [account for account in GoogleTaskAccount if account != failed]
    assert len(sent) == 1
    assert isinstance(sent[0], SendTelegramMessageEventGrid)
    assert failed.value in sent[0].message
    assert "sensitive-token" not in sent[0].message


def test_legacy_and_invalid_event_account(monkeypatch):
    resolved = []
    sent = []
    client = Mock()
    monkeypatch.setattr(
        usecases,
        "resolve_complete_task",
        lambda account=GoogleTaskAccount.Original: (
            resolved.append(account) or usecases.complete_task.Handler(client)
        ),
    )
    monkeypatch.setattr(shared, "send_eventgrid_events", lambda events: sent.extend(events))
    payload = {"tasklist": TaskLists.Default.value, "task_id": "id"}

    complete.complete_task.build().get_user_function()(_event(payload))
    complete.complete_task.build().get_user_function()(
        _event({**payload, "account": "unrecognized"})
    )

    assert resolved == [GoogleTaskAccount.Original]
    client.patch_task.assert_called_once()
    assert len(sent) == 1
    assert isinstance(sent[0], SendTelegramMessageEventGrid)
    assert "ValidationError" in sent[0].message


def test_second_account_failure_is_reported_without_secrets(monkeypatch):
    sent = []
    client = Mock()
    client.patch_task.side_effect = RuntimeError("sensitive-token")
    monkeypatch.setattr(
        usecases,
        "resolve_complete_task",
        lambda account: usecases.complete_task.Handler(client),
    )
    monkeypatch.setattr(shared, "send_eventgrid_events", lambda events: sent.extend(events))

    complete.complete_task.build().get_user_function()(
        _event(
            {
                "tasklist": TaskLists.Default.value,
                "task_id": "id",
                "account": "second",
            }
        )
    )

    assert len(sent) == 1
    assert "second" in sent[0].message
    assert "sensitive-token" not in sent[0].message


def test_publishing_failure_does_not_stop_next_account(monkeypatch):
    processed = []
    sent = []

    def resolve(account):
        processed.append(account)
        client = Mock()
        client.get_tasks.return_value = [
            Task(id="id", tasklist=TaskLists.Default, title=account.value)
        ]
        return Handler(client)

    def send(events):
        if isinstance(events[0], SendTelegramMessageEventGrid):
            sent.extend(events)
        elif events[0].account == GoogleTaskAccount.Original:
            raise RuntimeError("sensitive-token")
        else:
            sent.extend(events)

    monkeypatch.setattr(timer, "resolve_set_missing_task_due_date", resolve)
    monkeypatch.setattr(timer, "send_eventgrid_events", send)
    timer.set_missing_task_due_date.build().get_user_function()(None)

    assert processed == list(GoogleTaskAccount)
    assert sent[0].account == GoogleTaskAccount.Second
    assert "original" in sent[1].message
    assert "sensitive-token" not in sent[1].message
