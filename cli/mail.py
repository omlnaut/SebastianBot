import argparse
import json
import sys
from typing import Mapping, Protocol, Sequence

from sebastian.clients.google.credentials import (
    CredentialsError,
    load_credentials_from_env,
)
from sebastian.clients.google.gmail.client import GmailClient
from sebastian.clients.google.gmail.errors import GmailApiError, GmailAuthError
from sebastian.domain.gmail import Label, MailHit, SearchPage

DEFAULT_LIMIT = 25
MAX_LIMIT = 200


class GmailReadService(Protocol):
    """The read-only Gmail surface the CLI adapts to JSON."""

    def search(
        self, query: str, limit: int, page_token: str | None
    ) -> SearchPage: ...

    def labels(self) -> list[Label]: ...


class UsageError(Exception):
    """Raised when argv does not describe a valid invocation."""


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:  # type: ignore[override]
        raise UsageError(message)


def run(argv: Sequence[str], service: GmailReadService) -> int:
    """Run one invocation against the injected service and return an exit code."""
    command = _peek_command(argv)
    try:
        args = _build_parser().parse_args(list(argv))
        command = args.command
        if command == "search":
            return _search(args, service)
        return _labels(service)
    except UsageError as error:
        return _emit_error(command, "usage", str(error), exit_code=2)
    except GmailAuthError as error:
        return _emit_error(command, "auth", str(error))
    except GmailApiError as error:
        return _emit_error(command, "api", str(error))


def main(argv: Sequence[str] | None = None, service_factory=None) -> int:
    """Build the real service from the environment, then run."""
    arguments = list(sys.argv[1:] if argv is None else argv)
    command = _peek_command(arguments)
    factory = service_factory or build_service_from_env
    try:
        service = factory()
    except CredentialsError as error:
        return _emit_error(command, "auth", str(error))
    return run(arguments, service)


def build_service_from_env(env: Mapping[str, str] | None = None) -> GmailClient:
    return GmailClient(load_credentials_from_env(env))


def _build_parser() -> argparse.ArgumentParser:
    parser = _Parser(prog="seamail")
    commands = parser.add_subparsers(dest="command", required=True)

    search = commands.add_parser("search")
    search.add_argument("query")
    search.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    search.add_argument("--page-token", dest="page_token")

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
    if limit < 1:
        raise UsageError("--limit must be at least 1")
    return min(limit, MAX_LIMIT)


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


def _emit_error(command: str | None, kind: str, message: str, exit_code: int = 1) -> int:
    error = {"command": command, "error": {"kind": kind, "message": message}}
    print(json.dumps(error), file=sys.stderr)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
