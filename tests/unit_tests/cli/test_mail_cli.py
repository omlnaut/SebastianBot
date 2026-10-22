import json

from cli.mail import build_service_from_env, main, run
from sebastian.clients.google.credentials import ENV_VAR
from sebastian.clients.google.gmail.errors import GmailApiError
from sebastian.domain.gmail import AttachmentInfo, Label, MailHit, SearchPage, ShownMail


class _FakeService:
    def __init__(
        self,
        page: SearchPage | None = None,
        labels: list[Label] | None = None,
        shown: ShownMail | None = None,
    ):
        self._page = page if page is not None else SearchPage([], None, None)
        self._labels = labels or []
        self._shown = shown

    def search(self, query: str, limit: int, page_token: str | None) -> SearchPage:
        return self._page

    def show(self, message_id: str, body_format: str, max_chars: int) -> ShownMail:
        assert self._shown is not None
        return self._shown

    def labels(self) -> list[Label]:
        return self._labels


class _EchoService:
    """Echoes the request it received back into nextPageToken, so stdout reveals the plumbing."""

    def search(self, query: str, limit: int, page_token: str | None) -> SearchPage:
        return SearchPage([], f"echo:{query}|{limit}|{page_token}", None)

    def show(self, message_id: str, body_format: str, max_chars: int) -> ShownMail:
        return ShownMail(
            hit=_hit(),
            body=f"echo:{message_id}|{body_format}|{max_chars}",
            body_format=body_format,
            truncated=False,
        )

    def labels(self) -> list[Label]:
        return []


class _FailingService:
    def search(self, query: str, limit: int, page_token: str | None) -> SearchPage:
        raise GmailApiError("gmail boom", 500)

    def show(self, message_id: str, body_format: str, max_chars: int) -> ShownMail:
        raise GmailApiError("Requested entity was not found.", 404)

    def labels(self) -> list[Label]:
        return []


def _hit() -> MailHit:
    return MailHit(
        id="m1",
        thread_id="t1",
        sender="Alice Example <alice@example.com>",
        to=["bob@example.com"],
        cc=["Dave <dave@example.com>"],
        subject="Plain text hello",
        date="2026-10-14T09:12:03+00:00",
        internal_date="1760430723000",
        labels=["Inbox", "Klima"],
        label_ids=["INBOX", "Label_1"],
        snippet="a short snippet",
        size_estimate=48213,
        has_attachments=True,
        attachments=[AttachmentInfo("Rechnung.pdf", "application/pdf", 91234)],
    )


def _error(capsys) -> dict:
    return json.loads(capsys.readouterr().err)


def _shown(body: str = "the body", truncated: bool = False) -> ShownMail:
    return ShownMail(hit=_hit(), body=body, body_format="text", truncated=truncated)


def test_search_emits_one_json_object_with_the_shared_hit_shape(capsys):
    service = _FakeService(SearchPage([_hit()], "next-token", 12))

    code = run(["search", "from:alice"], service)

    assert code == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert json.loads(captured.out) == {
        "command": "search",
        "query": "from:alice",
        "limit": 25,
        "count": 1,
        "resultSizeEstimate": 12,
        "nextPageToken": "next-token",
        "hits": [
            {
                "id": "m1",
                "threadId": "t1",
                "from": "Alice Example <alice@example.com>",
                "to": ["bob@example.com"],
                "cc": ["Dave <dave@example.com>"],
                "subject": "Plain text hello",
                "date": "2026-10-14T09:12:03+00:00",
                "internalDate": "1760430723000",
                "labels": ["Inbox", "Klima"],
                "labelIds": ["INBOX", "Label_1"],
                "snippet": "a short snippet",
                "sizeEstimate": 48213,
                "hasAttachments": True,
                "attachments": [
                    {
                        "filename": "Rechnung.pdf",
                        "mimeType": "application/pdf",
                        "size": 91234,
                    }
                ],
            }
        ],
    }


def test_search_defaults_to_a_limit_of_25(capsys):
    run(["search", "x"], _EchoService())

    assert json.loads(capsys.readouterr().out)["limit"] == 25


def test_search_honours_an_explicit_lower_limit(capsys):
    run(["search", "x", "--limit", "3"], _EchoService())

    assert json.loads(capsys.readouterr().out)["limit"] == 3


def test_search_clamps_a_limit_above_the_cap(capsys):
    run(["search", "x", "--limit", "500"], _EchoService())

    assert json.loads(capsys.readouterr().out)["limit"] == 200


def test_search_forwards_the_page_token_and_returns_next_page_token(capsys):
    run(["search", "x", "--page-token", "token-abc"], _EchoService())

    out = json.loads(capsys.readouterr().out)
    assert out["nextPageToken"] == "echo:x|25|token-abc"


def test_labels_returns_id_name_type_and_visibility(capsys):
    service = _FakeService(
        labels=[Label(id="INBOX", name="Inbox", type="system", visibility="labelShow")]
    )

    code = run(["labels"], service)

    assert code == 0
    assert json.loads(capsys.readouterr().out) == {
        "command": "labels",
        "labels": [
            {
                "id": "INBOX",
                "name": "Inbox",
                "type": "system",
                "visibility": "labelShow",
            }
        ],
    }


def test_show_emits_one_json_object_with_the_hit_shape_plus_body(capsys):
    service = _FakeService(shown=_shown(body="the body", truncated=False))

    code = run(["show", "m1"], service)

    assert code == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert json.loads(captured.out) == {
        "command": "show",
        "message": {
            "id": "m1",
            "threadId": "t1",
            "from": "Alice Example <alice@example.com>",
            "to": ["bob@example.com"],
            "cc": ["Dave <dave@example.com>"],
            "subject": "Plain text hello",
            "date": "2026-10-14T09:12:03+00:00",
            "internalDate": "1760430723000",
            "labels": ["Inbox", "Klima"],
            "labelIds": ["INBOX", "Label_1"],
            "snippet": "a short snippet",
            "sizeEstimate": 48213,
            "hasAttachments": True,
            "attachments": [
                {
                    "filename": "Rechnung.pdf",
                    "mimeType": "application/pdf",
                    "size": 91234,
                }
            ],
            "body": "the body",
            "bodyFormat": "text",
            "truncated": False,
        },
    }


def test_show_reports_a_truncated_body(capsys):
    service = _FakeService(shown=_shown(body="cut here", truncated=True))

    run(["show", "m1"], service)

    message = json.loads(capsys.readouterr().out)["message"]
    assert message["body"] == "cut here"
    assert message["truncated"] is True


def test_show_defaults_to_text_and_a_20000_character_limit(capsys):
    run(["show", "m1"], _EchoService())

    message = json.loads(capsys.readouterr().out)["message"]
    assert message["bodyFormat"] == "text"
    assert message["body"] == "echo:m1|text|20000"


def test_show_opts_into_html(capsys):
    run(["show", "m1", "--format", "html"], _EchoService())

    message = json.loads(capsys.readouterr().out)["message"]
    assert message["bodyFormat"] == "html"


def test_show_forwards_an_explicit_max_chars(capsys):
    run(["show", "m1", "--max-chars", "120"], _EchoService())

    message = json.loads(capsys.readouterr().out)["message"]
    assert message["body"] == "echo:m1|text|120"


def test_show_rejects_an_unknown_body_format(capsys):
    code = run(["show", "m1", "--format", "markdown"], _FakeService())

    assert code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    error = json.loads(captured.err)
    assert error["command"] == "show"
    assert error["error"]["kind"] == "usage"


def test_show_rejects_a_max_chars_below_one(capsys):
    code = run(["show", "m1", "--max-chars", "0"], _FakeService())

    assert code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    error = json.loads(captured.err)
    assert error["command"] == "show"
    assert error["error"]["kind"] == "usage"
    assert "--max-chars" in error["error"]["message"]


def test_search_rejects_a_limit_below_one(capsys):
    code = run(["search", "x", "--limit", "0"], _FakeService())

    assert code == 2
    error = _error(capsys)
    assert error["command"] == "search"
    assert error["error"]["kind"] == "usage"


def test_usage_errors_are_reported_before_credentials_are_loaded(capsys):
    def factory():
        raise AssertionError("an invalid invocation must not build the service")

    code = main(["show", "m1", "--max-chars", "0"], service_factory=factory)

    assert code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert json.loads(captured.err)["error"]["kind"] == "usage"


def test_show_without_a_message_id_is_a_usage_error(capsys):
    code = run(["show"], _FakeService())

    assert code == 2
    assert _error(capsys)["error"]["kind"] == "usage"


def test_show_with_an_unknown_message_id_is_an_api_error(capsys):
    code = run(["show", "nope"], _FailingService())

    assert code == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert json.loads(captured.err) == {
        "command": "show",
        "error": {"kind": "api", "message": "Requested entity was not found."},
    }


def test_unknown_flag_is_a_usage_error_on_stderr(capsys):
    code = run(["search", "x", "--nope"], _FakeService())

    assert code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert json.loads(captured.err) == {
        "command": "search",
        "error": {"kind": "usage", "message": "unrecognized arguments: --nope"},
    }


def test_missing_query_is_a_usage_error(capsys):
    code = run(["search"], _FakeService())

    assert code == 2
    assert _error(capsys)["error"]["kind"] == "usage"


def test_missing_command_is_a_usage_error(capsys):
    code = run([], _FakeService())

    assert code == 2
    assert _error(capsys)["error"]["kind"] == "usage"


def test_api_failure_is_json_on_stderr_with_exit_code_1(capsys):
    code = run(["search", "x"], _FailingService())

    assert code == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert json.loads(captured.err) == {
        "command": "search",
        "error": {"kind": "api", "message": "gmail boom"},
    }


def test_missing_credentials_is_auth_error_naming_the_variable(capsys):
    code = main(["search", "x"], service_factory=lambda: build_service_from_env({}))

    assert code == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    error = json.loads(captured.err)
    assert error["command"] == "search"
    assert error["error"]["kind"] == "auth"
    assert ENV_VAR in error["error"]["message"]


def test_invalid_credentials_json_is_auth_error(capsys):
    code = main(
        ["labels"],
        service_factory=lambda: build_service_from_env({ENV_VAR: "{not json"}),
    )

    assert code == 1
    error = _error(capsys)
    assert error["command"] == "labels"
    assert error["error"]["kind"] == "auth"
    assert ENV_VAR in error["error"]["message"]
