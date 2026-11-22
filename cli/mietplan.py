"""`seadepot`: a JSON-only host CLI over the Mietplan webdepot.

One invocation prints exactly one JSON object on stdout. Failures are JSON on
stderr with a machine-readable `kind` (``auth``/``api``/``usage``/``io``) and the
documented exit code (0 ok, 1 runtime, 2 usage). Structurally this mirrors
`cli/mail.py`; the two CLIs share conventions, not code.
"""

import argparse
import json
import sys
from datetime import date, datetime
from typing import Callable, Mapping, Protocol, Sequence

import requests

from sebastian.clients.mietplan.client.client import MietplanClient
from sebastian.clients.mietplan.env_credentials import (
    CredentialsError,
    load_credentials_from_env,
)
from sebastian.clients.mietplan.errors import MietplanAuthError
from sebastian.domain.mietplan import (
    MietplanFile,
    MietplanFolder,
    MietplanWalk,
)

DEFAULT_LIMIT = 50
MAX_LIMIT = 500


class MietplanService(Protocol):
    """The Mietplan surface the CLI adapts to JSON: one tolerant tree walk."""

    def walk_tolerant(self) -> MietplanWalk: ...


class UsageError(Exception):
    """Raised when argv does not describe a valid invocation."""


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:  # type: ignore[override]
        raise UsageError(message)


def run(argv: Sequence[str], service: MietplanService) -> int:
    """Run one invocation against the injected service and return an exit code."""
    try:
        args = _parse_args(argv)
    except UsageError as error:
        return _emit_error(_peek_command(argv), "usage", str(error), exit_code=2)
    return _dispatch(args, service)


def main(
    argv: Sequence[str] | None = None,
    service_factory: Callable[[], MietplanClient] | None = None,
) -> int:
    """Validate argv, build the real service from the environment, then run."""
    arguments = list(sys.argv[1:] if argv is None else argv)
    try:
        args = _parse_args(arguments)
    except UsageError as error:
        return _emit_error(_peek_command(arguments), "usage", str(error), exit_code=2)
    factory: Callable[[], MietplanClient] = service_factory or build_service_from_env
    try:
        service = factory()
    except (CredentialsError, MietplanAuthError) as error:
        return _emit_error(args.command, "auth", str(error))
    except requests.RequestException as error:
        return _emit_error(args.command, "api", str(error))
    return _dispatch(args, service)


def build_service_from_env(env: Mapping[str, str] | None = None) -> MietplanClient:
    return MietplanClient(load_credentials_from_env(env))


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    return _build_parser().parse_args(list(argv))


def _dispatch(args: argparse.Namespace, service: MietplanService) -> int:
    command = args.command
    try:
        if command == "search":
            return _search(args, service)
        raise UsageError(f"unknown command: {command}")
    except UsageError as error:
        return _emit_error(command, "usage", str(error), exit_code=2)
    except MietplanAuthError as error:
        return _emit_error(command, "auth", str(error))
    except requests.RequestException as error:
        return _emit_error(command, "api", str(error))
    except OSError as error:
        return _emit_error(command, "io", str(error))


def _build_parser() -> argparse.ArgumentParser:
    parser = _Parser(prog="seadepot")
    commands = parser.add_subparsers(dest="command", required=True)

    search = commands.add_parser(
        "search",
        help="walk the webdepot tree and print the files that match",
        description=(
            "Walk the whole webdepot tree and filter locally. The walk always runs "
            "to completion; --limit only truncates the printed result list."
        ),
    )
    search.add_argument(
        "substring",
        nargs="?",
        help="case-insensitive substring of the file's folder/path/name",
    )
    search.add_argument(
        "--folder",
        metavar="PREFIX",
        help="keep only files whose folder path starts with this prefix "
        "(matched path segment by path segment, not as a substring)",
    )
    search.add_argument(
        "--after",
        type=_parse_date,
        metavar="YYYY-MM-DD",
        help="keep files created on or after this date (inclusive)",
    )
    search.add_argument(
        "--before",
        type=_parse_date,
        metavar="YYYY-MM-DD",
        help="keep files created on or before this date (inclusive)",
    )
    search.add_argument(
        "--limit",
        type=_at_least_one,
        default=DEFAULT_LIMIT,
        help=(
            f"how many files to print (default {DEFAULT_LIMIT}, capped at "
            f"{MAX_LIMIT}); the walk itself is never truncated"
        ),
    )

    # Ticket #129 adds the `download` subcommand here.

    return parser


def _search(args: argparse.Namespace, service: MietplanService) -> int:
    limit = _effective_limit(args.limit)
    walk = service.walk_tolerant()
    matched = _matching_files(walk, args)
    returned = matched[:limit]
    _emit(
        {
            "command": "search",
            "filters": {
                "substring": args.substring,
                "folder": args.folder,
                "after": _iso(args.after),
                "before": _iso(args.before),
                "limit": limit,
            },
            "count": len(returned),
            "scannedFolders": len(walk.folders),
            "truncated": len(matched) > limit,
            "files": [_file_json(folder, file) for folder, file in returned],
            "warnings": [
                {
                    "folderId": warning.folder_id,
                    "path": _join(warning.path),
                    "error": warning.error,
                }
                for warning in walk.warnings
            ],
        }
    )
    return 0


def _matching_files(
    walk: MietplanWalk, args: argparse.Namespace
) -> list[tuple[MietplanFolder, MietplanFile]]:
    """Every file that passes the filters, in walk order, before the limit."""
    substring: str | None = args.substring
    needle = substring.lower() if substring else None
    prefix = _path_segments(args.folder or "")
    return [
        (folder, file)
        for folder in walk.folders
        for file in folder.files
        if _matches(folder, file, needle, prefix, args.after, args.before)
    ]


def _matches(
    folder: MietplanFolder,
    file: MietplanFile,
    needle: str | None,
    prefix: Sequence[str],
    after: date | None,
    before: date | None,
) -> bool:
    path = [*folder.path, file.name]
    if needle is not None and needle not in _join(path).lower():
        return False
    if prefix and list(path[: len(prefix)]) != prefix:
        return False
    created = file.creation_date.date()
    if after is not None and created < after:
        return False
    if before is not None and created > before:
        return False
    return True


def _path_segments(prefix: str) -> list[str]:
    return [segment for segment in prefix.split("/") if segment]


def _file_json(folder: MietplanFolder, file: MietplanFile) -> dict[str, object]:
    return {
        "path": _join([*folder.path, file.name]),
        "folderId": folder.id,
        "name": file.name,
        "creationDate": file.creation_date.date().isoformat(),
        "url": file.url,
    }


def _join(path: Sequence[str]) -> str:
    return "/".join(path)


def _iso(value: date | None) -> str | None:
    return None if value is None else value.isoformat()


def _effective_limit(limit: int) -> int:
    return min(limit, MAX_LIMIT)


def _parse_date(raw: str) -> date:
    """An argparse type accepting exactly ``YYYY-MM-DD`` (no lenient forms)."""
    message = f"invalid date: {raw} (expected YYYY-MM-DD)"
    try:
        parsed = datetime.strptime(raw, "%Y-%m-%d").date()
    except ValueError:
        raise argparse.ArgumentTypeError(message) from None
    if parsed.isoformat() != raw:
        raise argparse.ArgumentTypeError(message)
    return parsed


def _at_least_one(raw: str) -> int:
    """An argparse type that rejects non-positive numbers as a usage error."""
    try:
        value = int(raw)
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid integer: {raw}") from None
    if value < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return value


def _peek_command(argv: Sequence[str]) -> str | None:
    if argv and not argv[0].startswith("-"):
        return argv[0]
    return None


def _emit(payload: dict[str, object]) -> None:
    print(json.dumps(payload), file=sys.stdout)


def _emit_error(
    command: str | None,
    kind: str,
    message: str,
    exit_code: int = 1,
) -> int:
    error: dict[str, object] = {"kind": kind, "message": message}
    print(json.dumps({"command": command, "error": error}), file=sys.stderr)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
