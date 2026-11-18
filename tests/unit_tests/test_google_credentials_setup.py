import json
import stat
import sys
from unittest.mock import Mock

import pytest

from investigations.google_token import create_credentials


def test_second_account_authorization_uses_tasks_scope_and_private_file(
    monkeypatch, tmp_path
):
    output = tmp_path / "second.json"
    credentials = Mock()
    credentials.to_json.return_value = json.dumps({"refresh_token": "example"})
    flow = Mock()
    flow.run_local_server.return_value = credentials
    factory = Mock(return_value=flow)
    monkeypatch.setattr(
        create_credentials.InstalledAppFlow, "from_client_secrets_file", factory
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["create_credentials.py", "--tasks-only", "--output", str(output)],
    )

    create_credentials.main()

    assert factory.call_args.args[1] == ["https://www.googleapis.com/auth/tasks"]
    assert json.loads(output.read_text()) == {
        "credentials": {"refresh_token": "example"}
    }
    assert stat.S_IMODE(output.stat().st_mode) == 0o600
    with pytest.raises(FileExistsError):
        create_credentials.main()
