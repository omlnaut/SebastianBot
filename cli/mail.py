import argparse
import json
import sys
from typing import Mapping, Protocol, Sequence

from sebastian.clients.google.credentials import (
    CredentialsError,
    load_credentials_from_env,
)
from sebastian.clients.google.gmail.body import BODY_FORMAT_TEXT, BODY_FORMATS
from sebastian.clients.google.gmail.client import GmailClient
from sebastian.clients.google.gmail.errors import (
    AttachmentWriteError,
    GmailApiError,
    GmailAuthError,
)
from sebastian.domain.gmail import (
    Label,
    MailHit,
    SearchPage,
    ShownMail,
    WrittenAttachment,
)

DEFAULT_LIMIT = 25
MAX_LIMIT = 200
DEFAULT_MAX_CHARS = 20000


class GmailReadService(Protocol):
    """The read-only Gmail surface the CLI adapts to JSON."""

    def search(self, query: str, limit: int, page_token: str | None) -> SearchPage: ...

    def show(self, message_id: str, body_format: str, max_chars: int) -> ShownMail: ...

    def save_attachments(
        self, message_id: str, out_dir: str, force: bool
    ) -> list[WrittenAttachment]: ...

    def labels(self) -> list[Label]: ...


class UsageError(Exception):
    """Raised when argv does not describe a valid invocation."""


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:  # type: ignore[override]
        raise UsageError(message)


def run(argv: Sequence[str], service: GmailReadService) -> int:
    """Run one invocation against the injected service and return an exit code."""
    try:
        args = _parse_args(argv)
    except UsageError as error:
        return _emit_error(_peek_command(argv), "usage", str(error), exit_code=2)
    return _dispatch(args, service)


def main(argv: Sequence[str] | None = None, service_factory=None) -> int:
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
    return _dispatch(args, service)


def build_service_from_env(env: Mapping[str, str] | None = None) -> GmailClient:
    return GmailClient(load_credentials_from_env(env))


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    return _build_parser().parse_args(list(argv))


def _dispatch(args: argparse.Namespace, service: GmailReadService) -> int:
    command = args.command
    try:
        if command == "search":
            return _search(args, service)
        if command == "show":
            return _show(args, service)
        if command == "attachments":
            return _attachments(args, service)
        return _labels(service)
    except UsageError as error:
        return _emit_error(command, "usage", str(error), exit_code=2)
    except GmailAuthError as error:
        return _emit_error(command, "auth", str(error))
    except GmailApiError as error:
        return _emit_error(command, "api", str(error))
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
    attachments.add_argument("--out", required=True)
    attachments.add_argument("--force", action="store_true")

    commands.add_parser("labels")

    return parser


def _search(args: argparse.Namespace, service: GmailReadService) -> int:
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


def _show(args: argparse.Namespace, service: GmailReadService) -> int:
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


def _attachments(args: argparse.Namespace, service: GmailReadService) -> int:
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


def _labels(service: GmailReadService) -> int:
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
    command: str | None, kind: str, message: str, exit_code: int = 1
) -> int:
    error = {"command": command, "error": {"kind": kind, "message": message}}
    print(json.dumps(error), file=sys.stderr)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
