import io
import json
from pathlib import Path

from cli.mail import build_service_from_env, main, run
from sebastian.clients.google.credentials import ENV_VAR
from sebastian.clients.google.gmail.errors import (
    AttachmentWriteError,
    GmailApiError,
    GmailAuthError,
)
from sebastian.domain.gmail import (
    AttachmentInfo,
    ComposedDraft,
    CreatedDraft,
    Label,
    MailHit,
    ReplyContext,
    SearchPage,
    ShownMail,
    WrittenAttachment,
)


class _DraftUnsupported:
    """Read-only fakes reach a draft method only if the CLI is wired wrong."""

    def reply_context(self, message_id: str) -> ReplyContext:
        raise AssertionError("reply_context must not be called")

    def own_address(self) -> str:
        raise AssertionError("own_address must not be called")

    def create_draft(self, draft: ComposedDraft) -> CreatedDraft:
        raise AssertionError("create_draft must not be called")


class _FakeService(_DraftUnsupported):
    def __init__(
        self,
        page: SearchPage | None = None,
        labels: list[Label] | None = None,
        shown: ShownMail | None = None,
        written: list[WrittenAttachment] | None = None,
    ):
        self._page = page if page is not None else SearchPage([], None, None)
        self._labels = labels or []
        self._shown = shown
        self._written = written or []

    def search(self, query: str, limit: int, page_token: str | None) -> SearchPage:
        return self._page

    def show(self, message_id: str, body_format: str, max_chars: int) -> ShownMail:
        assert self._shown is not None
        return self._shown

    def save_attachments(
        self, message_id: str, out_dir: str, force: bool
    ) -> list[WrittenAttachment]:
        return self._written

    def labels(self) -> list[Label]:
        return self._labels


class _EchoService(_DraftUnsupported):
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

    def save_attachments(
        self, message_id: str, out_dir: str, force: bool
    ) -> list[WrittenAttachment]:
        return [WrittenAttachment(f"echo:{message_id}|{out_dir}|{force}", 1)]

    def labels(self) -> list[Label]:
        return []


class _FailingService(_DraftUnsupported):
    def search(self, query: str, limit: int, page_token: str | None) -> SearchPage:
        raise GmailApiError("gmail boom", 500)

    def show(self, message_id: str, body_format: str, max_chars: int) -> ShownMail:
        raise GmailApiError("Requested entity was not found.", 404, "notFound")

    def save_attachments(
        self, message_id: str, out_dir: str, force: bool
    ) -> list[WrittenAttachment]:
        raise GmailApiError("Requested entity was not found.", 404, "notFound")

    def labels(self) -> list[Label]:
        return []


class _ExpiredTokenService(_FailingService):
    def search(self, query: str, limit: int, page_token: str | None) -> SearchPage:
        raise GmailAuthError("Invalid Credentials", 401, "authError")


class _UnwritableService(_FailingService):
    def save_attachments(
        self, message_id: str, out_dir: str, force: bool
    ) -> list[WrittenAttachment]:
        raise AttachmentWriteError(f"could not create output directory: {out_dir}")


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
        "error": {
            "kind": "api",
            "status": 404,
            "reason": "notFound",
            "message": "Requested entity was not found.",
        },
    }


def test_an_expired_token_is_reported_as_an_auth_error(capsys):
    code = run(["search", "x"], _ExpiredTokenService())

    assert code == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert json.loads(captured.err) == {
        "command": "search",
        "error": {
            "kind": "auth",
            "status": 401,
            "reason": "authError",
            "message": "Invalid Credentials",
        },
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
        "error": {"kind": "api", "status": 500, "message": "gmail boom"},
    }


def test_attachments_reports_written_paths_and_sizes(capsys, tmp_path):
    service = _FakeService(
        written=[
            WrittenAttachment(str(tmp_path / "Rechnung.pdf"), 91234),
            WrittenAttachment(str(tmp_path / "Anhang.txt"), 12),
        ]
    )

    code = run(["attachments", "m1", "--out", str(tmp_path)], service)

    assert code == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert json.loads(captured.out) == {
        "command": "attachments",
        "messageId": "m1",
        "files": [
            {"path": str(tmp_path / "Rechnung.pdf"), "size": 91234},
            {"path": str(tmp_path / "Anhang.txt"), "size": 12},
        ],
    }


def test_attachments_forwards_the_directory_and_force_flag(capsys):
    run(["attachments", "m1", "--out", "/tmp/out", "--force"], _EchoService())

    files = json.loads(capsys.readouterr().out)["files"]
    assert files == [{"path": "echo:m1|/tmp/out|True", "size": 1}]


def test_attachments_without_an_output_directory_is_a_usage_error(capsys):
    code = run(["attachments", "m1"], _FakeService())

    assert code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert json.loads(captured.err)["error"]["kind"] == "usage"


def test_attachments_with_an_unknown_message_id_is_an_api_error(capsys):
    code = run(["attachments", "nope", "--out", "/tmp/out"], _FailingService())

    assert code == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert json.loads(captured.err) == {
        "command": "attachments",
        "error": {
            "kind": "api",
            "status": 404,
            "reason": "notFound",
            "message": "Requested entity was not found.",
        },
    }


def test_attachments_filesystem_failure_is_an_io_error(capsys):
    code = run(["attachments", "m1", "--out", "/does/not/exist"], _UnwritableService())

    assert code == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert json.loads(captured.err) == {
        "command": "attachments",
        "error": {
            "kind": "io",
            "message": "could not create output directory: /does/not/exist",
        },
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


class _DraftService:
    """A draft-capable service: records what it was asked to create."""

    def __init__(
        self,
        context: ReplyContext | None = None,
        own_address: str = "me@example.com",
        create_error: Exception | None = None,
    ):
        self._context = context if context is not None else _reply_context()
        self._own_address = own_address
        self._create_error = create_error
        self.composed: list[ComposedDraft] = []
        self.context_ids: list[str] = []
        self.own_address_calls = 0

    def reply_context(self, message_id: str) -> ReplyContext:
        self.context_ids.append(message_id)
        return self._context

    def own_address(self) -> str:
        self.own_address_calls += 1
        return self._own_address

    def create_draft(self, draft: ComposedDraft) -> CreatedDraft:
        if self._create_error is not None:
            raise self._create_error
        self.composed.append(draft)
        return CreatedDraft(
            draft_id="r-1",
            message_id="m-new",
            thread_id=draft.request.thread_id or "thread-new",
        )


def _reply_context(**overrides) -> ReplyContext:
    fields = {
        "thread_id": "t1",
        "sender": "Alice Example <alice@example.com>",
        "to": ["me@example.com"],
        "cc": [],
        "subject": "Klimaanlage",
        "message_id_header": "<m1@example.com>",
        "references": None,
    }
    fields.update(overrides)
    return ReplyContext(**fields)


def _draft(argv: list[str], service: _DraftService, body: str = "Hallo.\n") -> int:
    return run(["draft", *argv], service, io.StringIO(body))


def test_draft_creates_the_draft_and_echoes_what_was_composed(capsys):
    service = _DraftService()

    code = _draft(
        ["--to", "alice@example.com", "--subject", "Kurzfrage"], service, "Hallo.\n"
    )

    assert code == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert json.loads(captured.out) == {
        "command": "draft",
        "dryRun": False,
        "draft": {"id": "r-1", "messageId": "m-new", "threadId": "thread-new"},
        "message": {
            "to": ["alice@example.com"],
            "cc": [],
            "bcc": [],
            "subject": "Kurzfrage",
            "bodyChars": 7,
            "attachments": [],
            "encodedBytes": service.composed[0].encoded_bytes,
        },
    }


def test_draft_takes_the_body_from_stdin_never_from_argv(capsys):
    service = _DraftService()

    _draft(["--to", "alice@example.com"], service, "Zeile eins\nZeile zwei\n")

    assert service.composed[0].request.body == "Zeile eins\nZeile zwei\n"
    assert json.loads(capsys.readouterr().out)["message"]["bodyChars"] == 22


def test_draft_reads_the_body_from_a_file(capsys, tmp_path: Path):
    body_file = tmp_path / "body.txt"
    body_file.write_text("Aus der Datei äöü.\n", encoding="utf-8")
    service = _DraftService()

    code = _draft(["--to", "alice@example.com", "--body-file", str(body_file)], service)

    assert code == 0
    assert service.composed[0].request.body == "Aus der Datei äöü.\n"


def test_draft_dry_run_composes_but_creates_nothing(capsys):
    service = _DraftService()

    code = _draft(["--to", "alice@example.com", "--dry-run"], service)

    assert code == 0
    assert service.composed == []
    out = json.loads(capsys.readouterr().out)
    assert out["dryRun"] is True
    assert out["draft"] is None
    assert out["message"]["to"] == ["alice@example.com"]


def test_draft_reply_derives_recipients_subject_and_thread(capsys):
    service = _DraftService()

    code = _draft(["--reply-to", "m1"], service)

    assert code == 0
    request = service.composed[0].request
    assert request.to == ["Alice Example <alice@example.com>"]
    assert request.subject == "Re: Klimaanlage"
    assert request.thread_id == "t1"
    assert request.in_reply_to == "<m1@example.com>"
    assert service.own_address_calls == 0


def test_draft_reply_all_asks_for_the_own_address_and_adds_the_original_copies(capsys):
    service = _DraftService(
        _reply_context(
            to=["Alice Example <alice@example.com>"], cc=["Dave <dave@example.com>"]
        )
    )

    _draft(["--reply-to", "m1", "--all"], service)

    request = service.composed[0].request
    assert service.own_address_calls == 1
    assert request.to == ["Alice Example <alice@example.com>"]
    assert request.cc == ["Dave <dave@example.com>"]


def test_draft_reply_keeps_an_explicit_cc_and_appends_it_to_the_derived_one(capsys):
    service = _DraftService(_reply_context(cc=["Dave <dave@example.com>"]))
    _draft(["--reply-to", "m1", "--all", "--cc", "erin@example.com"], service)

    assert service.composed[0].request.cc == [
        "Dave <dave@example.com>",
        "erin@example.com",
    ]


def test_draft_reply_honours_an_explicit_subject_override(capsys):
    service = _DraftService()

    _draft(["--reply-to", "m1", "--subject", "Anderer Betreff"], service)

    assert service.composed[0].request.subject == "Anderer Betreff"


def test_draft_echoes_an_attachment_with_its_visible_name(capsys, tmp_path: Path):
    path = tmp_path / "scan.pdf"
    path.write_bytes(b"%PDF-1.7 fake")
    service = _DraftService()

    _draft(
        [
            "--to",
            "alice@example.com",
            "--attach",
            str(path),
            "--attach-name",
            "scan.pdf=Rechnung Oktober.pdf",
        ],
        service,
    )

    assert json.loads(capsys.readouterr().out)["message"]["attachments"] == [
        {
            "path": str(path),
            "filename": "Rechnung Oktober.pdf",
            "mimeType": "application/pdf",
            "size": 13,
        }
    ]


def test_draft_requires_a_recipient_source(capsys):
    service = _DraftService()

    code = _draft(["--subject", "x"], service)

    assert code == 2
    error = _error(capsys)
    assert error["command"] == "draft"
    assert error["error"]["kind"] == "usage"
    assert "--to" in error["error"]["message"]


def test_draft_rejects_to_together_with_reply_to(capsys):
    code = _draft(["--reply-to", "m1", "--to", "alice@example.com"], _DraftService())

    assert code == 2
    assert "cannot be combined" in _error(capsys)["error"]["message"]


def test_draft_rejects_all_without_reply_to(capsys):
    code = _draft(["--to", "alice@example.com", "--all"], _DraftService())

    assert code == 2
    assert "--all needs --reply-to" in _error(capsys)["error"]["message"]


def test_draft_reports_an_unparseable_recipient_as_a_usage_error(capsys):
    code = _draft(["--to", "not an address"], _DraftService())

    assert code == 2
    assert "not a usable email address" in _error(capsys)["error"]["message"]


def test_draft_reports_a_missing_attachment_as_a_usage_error(capsys, tmp_path: Path):
    code = _draft(
        ["--to", "a@b.c", "--attach", str(tmp_path / "nope.pdf")], _DraftService()
    )

    assert code == 2
    error = _error(capsys)
    assert error["error"]["kind"] == "usage"
    assert "does not exist" in error["error"]["message"]


def test_draft_reports_an_unreadable_body_file_as_an_io_error(capsys, tmp_path: Path):
    code = _draft(
        ["--to", "a@b.c", "--body-file", str(tmp_path / "missing.txt")], _DraftService()
    )

    assert code == 1
    error = _error(capsys)
    assert error["error"]["kind"] == "io"
    assert "could not read body file" in error["error"]["message"]


def test_draft_reports_an_api_failure_when_creating(capsys):
    service = _DraftService(create_error=GmailApiError("Request too large", 400))

    code = _draft(["--to", "a@b.c"], service)

    assert code == 1
    error = _error(capsys)
    assert error["error"]["kind"] == "api"
    assert error["error"]["status"] == 400
