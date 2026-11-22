"""Resolve one search path against a walk and write it below an output directory."""

from pathlib import Path
from typing import Callable, Sequence

from sebastian.domain.mietplan import (
    MietplanFile,
    MietplanWalk,
    MietplanWalkWarning,
    WrittenMietplanFile,
)

from .errors import (
    MietplanDownloadIoError,
    MietplanFolderReadError,
    MietplanPathError,
    MietplanPathNotFoundError,
)


def download_to_dir(
    portal_path: str,
    out_dir: str | Path,
    force: bool,
    walk: Callable[[], MietplanWalk],
    fetch: Callable[[str], bytes],
) -> WrittenMietplanFile:
    """Write the file at ``portal_path`` under ``out_dir``, mirroring its folders."""
    raw_segments, safe_segments = _safe_segments(portal_path)
    tree = walk()
    matched = _find_file(tree, raw_segments)
    if matched is None:
        warning = _covering_warning(tree, raw_segments[:-1])
        if warning is not None:
            folder = "/".join(warning.path) or "/"
            raise MietplanFolderReadError(
                f'could not read webdepot folder "{folder}": {warning.error}'
            )
        raise MietplanPathNotFoundError(
            f'path not found in the webdepot: "{portal_path}"'
        )

    output_root = Path(out_dir).resolve()
    target = output_root.joinpath(*safe_segments)
    if not target.is_relative_to(output_root):
        raise MietplanPathError(
            f'unsafe path "{portal_path}": it escapes the output directory'
        )

    try:
        target.parent.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        raise MietplanDownloadIoError(
            f"could not create output directory {target.parent}: {error}"
        ) from error

    if target.exists() and not force:
        raise MietplanDownloadIoError(
            f"refusing to overwrite existing file: {target} "
            "(pass --force to overwrite)"
        )

    content = fetch(matched.url)
    try:
        target.write_bytes(content)
    except OSError as error:
        raise MietplanDownloadIoError(f"could not write {target}: {error}") from error
    return WrittenMietplanFile(
        portal_path=portal_path, path=str(target), size=len(content)
    )


def _safe_segments(portal_path: str) -> tuple[list[str], list[str]]:
    """Split a search path into matchable raw segments and safe target segments.

    The raw segments are what the portal walk actually reported, so resolution
    stays exact even when a real name has surrounding whitespace. The safe
    segments are what may be joined below ``--out``; anything that cannot be
    made safe is a usage error, never a replacement that silently changes where
    the file lands.
    """
    if portal_path.startswith(("/", "\\")):
        raise MietplanPathError(
            f'unsafe path "{portal_path}": it must be relative to the output directory'
        )
    raw_segments = portal_path.split("/")
    safe_segments: list[str] = []
    for raw in raw_segments:
        if not raw:
            raise MietplanPathError(
                f'unsafe path "{portal_path}": empty path segment'
            )
        if "\\" in raw:
            raise MietplanPathError(
                f'unsafe path "{portal_path}": backslashes are not allowed'
            )
        if any(not character.isprintable() for character in raw):
            raise MietplanPathError(
                f'unsafe path "{portal_path}": non-printable characters are not allowed'
            )
        safe = raw.strip()
        if safe in {"", ".", ".."}:
            raise MietplanPathError(
                f'unsafe path "{portal_path}": segment "{raw}" is not allowed'
            )
        safe_segments.append(safe)
    return raw_segments, safe_segments


def _find_file(
    walk: MietplanWalk, raw_segments: Sequence[str]
) -> MietplanFile | None:
    wanted = "/".join(raw_segments)
    for folder in walk.folders:
        for file in folder.files:
            if "/".join([*folder.path, file.name]) == wanted:
                return file
    return None


def _covering_warning(
    walk: MietplanWalk, folder_segments: Sequence[str]
) -> MietplanWalkWarning | None:
    """The deepest unreadable folder that could have held the requested file."""
    covering = [
        warning
        for warning in walk.warnings
        if list(folder_segments[: len(warning.path)]) == warning.path
    ]
    if not covering:
        return None
    return max(covering, key=lambda warning: len(warning.path))
