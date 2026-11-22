"""D10: a rejected login must fail loudly instead of producing an empty result.

V1 (recorded in docs/specs/mietplan-verification.md): an unauthenticated
`getFolders` request answers HTTP 403 with an empty HTML body, so the probe keys
off the status code and off "the body is not JSON", never off login-form markup.
"""

import pytest
import requests

from sebastian.clients.mietplan.client import client as client_module
from sebastian.clients.mietplan.client._verify_session import verify_session
from sebastian.clients.mietplan.client.client import MietplanClient
from sebastian.clients.mietplan.credentials import MietplanCredentials
from sebastian.clients.mietplan.errors import MietplanAuthError
from tests.unit_tests.clients.mietplan._portal import (
    TOP,
    FakeSession,
    empty,
    folders,
    not_json,
)

CREDENTIALS = MietplanCredentials(username="me@example.com", password="geheim")


def test_a_readable_tree_passes_the_probe():
    session = FakeSession({("folders", TOP): empty()})

    verify_session(session, TOP)

    assert session.requests == [("folders", TOP)]


def test_a_403_with_an_empty_html_body_is_a_rejected_login():
    """The signal an unauthenticated getFolders actually produces on the portal."""
    session = FakeSession({("folders", TOP): not_json(text="", status_code=403)})

    with pytest.raises(MietplanAuthError, match="403"):
        verify_session(session, TOP)


def test_a_login_page_instead_of_json_is_a_rejected_login():
    session = FakeSession({("folders", TOP): not_json("<html>login</html>")})

    with pytest.raises(MietplanAuthError) as raised:
        verify_session(session, TOP)

    assert "JSON" in str(raised.value)


def test_a_server_error_is_not_mistaken_for_a_rejected_login():
    session = FakeSession({("folders", TOP): not_json(text="", status_code=500)})

    with pytest.raises(requests.HTTPError):
        verify_session(session, TOP)


def test_a_connection_failure_is_not_mistaken_for_a_rejected_login():
    session = FakeSession({("folders", TOP): requests.ConnectionError("read timeout")})

    with pytest.raises(requests.ConnectionError):
        verify_session(session, TOP)


def test_the_client_logs_in_and_then_probes_the_root_folder(
    monkeypatch: pytest.MonkeyPatch,
):
    calls: list[str] = []
    session = FakeSession({("folders", TOP): folders(("A", "A"))})
    monkeypatch.setattr(
        client_module, "create_retry_session", lambda: session, raising=True
    )
    monkeypatch.setattr(
        client_module._login,
        "login",
        lambda session, username, password: calls.append(f"login:{username}"),
    )

    MietplanClient(CREDENTIALS)

    assert calls == ["login:me@example.com"]
    assert session.requests == [("folders", TOP)]


def test_the_client_refuses_a_rejected_login_instead_of_walking_an_empty_tree(
    monkeypatch: pytest.MonkeyPatch,
):
    session = FakeSession({("folders", TOP): not_json(text="", status_code=403)})
    monkeypatch.setattr(
        client_module, "create_retry_session", lambda: session, raising=True
    )
    monkeypatch.setattr(client_module._login, "login", lambda *args: None)

    with pytest.raises(MietplanAuthError):
        MietplanClient(CREDENTIALS)
