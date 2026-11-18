from unittest.mock import Mock

from cloud.dependencies import clients
from cloud.helper import SecretKeys
from sebastian.clients.google.task.client.client import GoogleTaskClient
from sebastian.clients.google.task.client.service_wrapper import TaskServiceWrapper
from sebastian.domain.task import GoogleTaskAccount, TaskLists


def test_second_account_uses_its_own_default_list(monkeypatch):
    service = Mock()
    service.get_default_tasklist_id.return_value = "second-list"
    service.get_tasks.return_value = []
    monkeypatch.setattr(
        "sebastian.clients.google.task.client.client.TaskServiceWrapper",
        lambda credentials: service,
    )
    client = GoogleTaskClient(Mock(), use_account_default=True)

    client.get_tasks()
    client.patch_task(TaskLists.Default, "task")

    assert service.get_tasks.call_args.args[0] == "second-list"
    assert service.patch_task.call_args.args[:2] == ("second-list", "task")
    assert service.get_default_tasklist_id.call_count == 2


def test_original_account_keeps_existing_default_list(monkeypatch):
    service = Mock()
    service.get_tasks.return_value = []
    monkeypatch.setattr(
        "sebastian.clients.google.task.client.client.TaskServiceWrapper",
        lambda credentials: service,
    )
    client = GoogleTaskClient(Mock())

    client.get_tasks()
    client.patch_task(TaskLists.Default, "task")

    assert service.get_tasks.call_args.args[0] == service.patch_task.call_args.args[0]
    assert service.get_tasks.call_args.args[0] != "second-list"
    service.get_default_tasklist_id.assert_not_called()


def test_default_tasklist_lookup_uses_google_default_alias(monkeypatch):
    service = Mock()
    service.tasklists.return_value.get.return_value.execute.return_value = {
        "kind": "tasks#taskList",
        "id": "second-list",
        "etag": "etag",
        "title": "Tasks",
    }
    monkeypatch.setattr(
        "sebastian.clients.google.task.client.service_wrapper.build",
        lambda *args, **kwargs: service,
    )

    assert TaskServiceWrapper(Mock()).get_default_tasklist_id() == "second-list"
    service.tasklists.return_value.get.assert_called_once_with(tasklist="@default")


def test_account_credential_selection(monkeypatch):
    used = []
    credential_model = Mock()
    monkeypatch.setattr(
        clients, "get_secret", lambda key: used.append(key) or credential_model
    )
    monkeypatch.setattr(
        clients.Credentials, "from_authorized_user_info", lambda info: Mock()
    )
    clients.load_google_credentials.cache_clear()
    try:
        clients.load_google_credentials(GoogleTaskAccount.Original)
        clients.load_google_credentials(GoogleTaskAccount.Second)
        assert used == [SecretKeys.GoogleCredentials, SecretKeys.GoogleCredentialsSecond]
    finally:
        clients.load_google_credentials.cache_clear()
