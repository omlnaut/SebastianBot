import argparse
import json
import sys
from pathlib import Path
from typing import Mapping, Protocol, Sequence, TextIO

from sebastian.clients.google.credentials import (
    CredentialsError,
    load_credentials_from_env,
)
from sebastian.clients.google.gmail.body import BODY_FORMAT_TEXT, BODY_FORMATS
from sebastian.clients.google.gmail.client import GmailClient
from sebastian.clients.google.gmail.compose import (
    compose_draft,
    derive_reply_target,
    parse_recipients,
    parse_renames,
    resolve_attachments,
)
from sebastian.clients.google.gmail.errors import (
    AttachmentWriteError,
    DraftInputError,
    DraftIoError,
    GmailApiError,
    GmailAuthError,
)
from sebastian.domain.gmail import (
    ComposedDraft,
    CreatedDraft,
    DraftRequest,
    Label,
    MailHit,
    ReplyContext,
    SearchPage,
    ShownMail,
    WrittenAttachment,
)

DEFAULT_LIMIT = 25
MAX_LIMIT = 200
DEFAULT_MAX_CHARS = 20000


class GmailService(Protocol):
    """The Gmail surface the CLI adapts to JSON: reads, plus draft creation."""

    def search(self, query: str, limit: int, page_token: str | None) -> SearchPage: ...

    def show(self, message_id: str, body_format: str, max_chars: int) -> ShownMail: ...

    def save_attachments(
        self, message_id: str, out_dir: str, force: bool
    ) -> list[WrittenAttachment]: ...

    def labels(self) -> list[Label]: ...

    def reply_context(self, message_id: str) -> ReplyContext: ...

    def own_address(self) -> str: ...

    def create_draft(self, draft: ComposedDraft) -> CreatedDraft: ...


class UsageError(Exception):
    """Raised when argv does not describe a valid invocation."""


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:  # type: ignore[override]
        raise UsageError(message)


def run(argv: Sequence[str], service: GmailService, stdin: TextIO | None = None) -> int:
    """Run one invocation against the injected service and return an exit code."""
    try:
        args = _parse_args(argv)
    except UsageError as error:
        return _emit_error(_peek_command(argv), "usage", str(error), exit_code=2)
    return _dispatch(args, service, stdin)


def main(
    argv: Sequence[str] | None = None, service_factory=None, stdin: TextIO | None = None
) -> int:
    """Validate argv, build the real service from the environment, then run."""
    arguments = list(sys.argv[1:] if argv is None else argv)
    try:
        args = _parse_args(arguments)
    except UsageError as error:
        return _emit_error(_peek_command(arguments), "usage", str(error), exit_code=2)
    factory = service_factory or build_service_from_env
    try:
        service = factory()
    except CredentialsError as error:
        return _emit_error(args.command, "auth", str(error))
    return _dispatch(args, service, stdin)


def build_service_from_env(env: Mapping[str, str] | None = None) -> GmailClient:
    return GmailClient(load_credentials_from_env(env))


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    return _build_parser().parse_args(list(argv))


def _dispatch(
    args: argparse.Namespace, service: GmailService, stdin: TextIO | None = None
) -> int:
    command = args.command
    try:
        if command == "search":
            return _search(args, service)
        if command == "show":
            return _show(args, service)
        if command == "attachments":
            return _attachments(args, service)
        if command == "draft":
            return _draft(args, service, stdin)
        return _labels(service)
    except UsageError as error:
        return _emit_error(command, "usage", str(error), exit_code=2)
    except DraftInputError as error:
        return _emit_error(command, "usage", str(error), exit_code=2)
    except DraftIoError as error:
        return _emit_error(command, "io", str(error))
    except GmailAuthError as error:
        return _emit_error(
            command,
            "auth",
            str(error),
            status=error.status,
            reason=error.reason,
        )
    except GmailApiError as error:
        return _emit_error(
            command,
            "api",
            str(error),
            status=error.status,
            reason=error.reason,
        )
    except AttachmentWriteError as error:
        return _emit_error(command, "io", str(error))


def _build_parser() -> argparse.ArgumentParser:
    parser = _Parser(prog="seamail")
    commands = parser.add_subparsers(dest="command", required=True)

    search = commands.add_parser("search")
    search.add_argument("query")
    search.add_argument("--limit", type=_at_least_one, default=DEFAULT_LIMIT)
    search.add_argument("--page-token", dest="page_token")

    show = commands.add_parser("show")
    show.add_argument("message_id")
    show.add_argument(
        "--format",
        dest="body_format",
        choices=BODY_FORMATS,
        default=BODY_FORMAT_TEXT,
    )
    show.add_argument(
        "--max-chars", dest="max_chars", type=_at_least_one, default=DEFAULT_MAX_CHARS
    )

    attachments = commands.add_parser("attachments")
    attachments.add_argument("message_id")
    attachments.add_argument(
        "--out",
        required=True,
        help="directory to write the attachments into (created if missing)",
    )
    attachments.add_argument("--force", action="store_true")

    commands.add_parser("labels")

    draft = commands.add_parser("draft")
    draft.add_argument("--to", action="append", default=[])
    draft.add_argument("--cc", action="append", default=[])
    draft.add_argument("--bcc", action="append", default=[])
    draft.add_argument("--subject")
    draft.add_argument(
        "--body-file",
        dest="body_file",
        help="read the body from this file instead of stdin",
    )
    draft.add_argument("--attach", action="append", default=[])
    draft.add_argument(
        "--attach-name",
        dest="attach_name",
        action="append",
        default=[],
        help="rename an attachment: <basename>=<newname>",
    )
    draft.add_argument(
        "--reply-to",
        dest="reply_to",
        help="message id to reply to; derives recipients, subject and thread",
    )
    draft.add_argument(
        "--all",
        action="store_true",
        help="with --reply-to: also include the original To and Cc recipients",
    )
    draft.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        help="validate and compose, but create nothing in Gmail",
    )

    return parser


def _search(args: argparse.Namespace, service: GmailService) -> int:
    limit = _effective_limit(args.limit)
    page = service.search(args.query, limit, args.page_token)
    _emit(
        {
            "command": "search",
            "query": args.query,
            "limit": limit,
            "count": len(page.hits),
            "resultSizeEstimate": page.result_size_estimate,
            "nextPageToken": page.next_page_token,
            "hits": [_hit_json(hit) for hit in page.hits],
        }
    )
    return 0


def _show(args: argparse.Namespace, service: GmailService) -> int:
    shown = service.show(args.message_id, args.body_format, args.max_chars)
    _emit(
        {
            "command": "show",
            "message": {
                **_hit_json(shown.hit),
                "body": shown.body,
                "bodyFormat": shown.body_format,
                "truncated": shown.truncated,
            },
        }
    )
    return 0


def _attachments(args: argparse.Namespace, service: GmailService) -> int:
    _emit(
        {
            "command": "attachments",
            "messageId": args.message_id,
            "files": [
                {"path": written.path, "size": written.size}
                for written in service.save_attachments(
                    args.message_id, args.out, args.force
                )
            ],
        }
    )
    return 0


def _labels(service: GmailService) -> int:
    _emit(
        {
            "command": "labels",
            "labels": [
                {
                    "id": label.id,
                    "name": label.name,
                    "type": label.type,
                    "visibility": label.visibility,
                }
                for label in service.labels()
            ],
        }
    )
    return 0


def _draft(
    args: argparse.Namespace, service: GmailService, stdin: TextIO | None
) -> int:
    _check_draft_flags(args)
    request = _draft_request(args, service, stdin)
    composed = compose_draft(request)
    created = None if args.dry_run else service.create_draft(composed)
    _emit(
        {
            "command": "draft",
            "dryRun": bool(args.dry_run),
            "draft": (
                None
                if created is None
                else {
                    "id": created.draft_id,
                    "messageId": created.message_id,
                    "threadId": created.thread_id,
                }
            ),
            "message": _draft_message_json(request, composed.encoded_bytes),
        }
    )
    return 0


def _check_draft_flags(args: argparse.Namespace) -> None:
    if args.reply_to and args.to:
        raise UsageError(
            "--to cannot be combined with --reply-to; a reply derives its recipients "
            "(--cc/--bcc may still be added)"
        )
    if args.all and not args.reply_to:
        raise UsageError("--all needs --reply-to")
    if not args.reply_to and not args.to:
        raise UsageError("draft needs --to, or --reply-to <message-id>")


def _draft_request(
    args: argparse.Namespace, service: GmailService, stdin: TextIO | None
) -> DraftRequest:
    body = _read_body(args.body_file, stdin)
    attachments = resolve_attachments(args.attach, parse_renames(args.attach_name))

    to = parse_recipients(args.to)
    derived_cc: list[str] = []
    subject = args.subject or ""
    thread_id: str | None = None
    in_reply_to: str | None = None
    references: str | None = None

    if args.reply_to:
        context = service.reply_context(args.reply_to)
        own_address = service.own_address() if args.all else None
        target = derive_reply_target(context, own_address, bool(args.all))
        to = target.to
        derived_cc = target.cc
        subject = args.subject or target.subject
        thread_id = target.thread_id
        in_reply_to = target.in_reply_to
        references = target.references

    return DraftRequest(
        to=to,
        cc=parse_recipients([*derived_cc, *args.cc]),
        bcc=parse_recipients(args.bcc),
        subject=subject,
        body=body,
        attachments=attachments,
        thread_id=thread_id,
        in_reply_to=in_reply_to,
        references=references,
    )


def _read_body(body_file: str | None, stdin: TextIO | None) -> str:
    """Read the draft body from a file or stdin, never from argv."""
    if body_file:
        try:
            return Path(body_file).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            detail = getattr(error, "strerror", None) or str(error)
            raise DraftIoError(
                f"could not read body file {body_file}: {detail}"
            ) from error
    source = sys.stdin if stdin is None else stdin
    return source.read()


def _draft_message_json(request: DraftRequest, encoded_bytes: int) -> dict:
    return {
        "to": request.to,
        "cc": request.cc,
        "bcc": request.bcc,
        "subject": request.subject,
        "bodyChars": len(request.body),
        "attachments": [
            {
                "path": attachment.path,
                "filename": attachment.filename,
                "mimeType": attachment.mime_type,
                "size": attachment.size,
            }
            for attachment in request.attachments
        ],
        "encodedBytes": encoded_bytes,
    }


def _effective_limit(limit: int) -> int:
    return min(limit, MAX_LIMIT)


def _at_least_one(raw: str) -> int:
    """An argparse type that rejects non-positive numbers as a usage error."""
    try:
        value = int(raw)
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid integer: {raw}") from None
    if value < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return value


def _hit_json(hit: MailHit) -> dict:
    return {
        "id": hit.id,
        "threadId": hit.thread_id,
        "from": hit.sender,
        "to": hit.to,
        "cc": hit.cc,
        "subject": hit.subject,
        "date": hit.date,
        "internalDate": hit.internal_date,
        "labels": hit.labels,
        "labelIds": hit.label_ids,
        "snippet": hit.snippet,
        "sizeEstimate": hit.size_estimate,
        "hasAttachments": hit.has_attachments,
        "attachments": [
            {
                "filename": attachment.filename,
                "mimeType": attachment.mime_type,
                "size": attachment.size,
            }
            for attachment in hit.attachments
        ],
    }


def _peek_command(argv: Sequence[str]) -> str | None:
    if argv and not argv[0].startswith("-"):
        return argv[0]
    return None


def _emit(payload: dict) -> None:
    print(json.dumps(payload), file=sys.stdout)


def _emit_error(
    command: str | None,
    kind: str,
    message: str,
    exit_code: int = 1,
    status: int | None = None,
    reason: str | None = None,
) -> int:
    error: dict[str, object] = {"kind": kind}
    if status is not None:
        error["status"] = status
    if reason is not None:
        error["reason"] = reason
    error["message"] = message
    print(json.dumps({"command": command, "error": error}), file=sys.stderr)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
