import os
from pathlib import Path
from typing import Callable, Sequence

from sebastian.clients.google.gmail.errors import AttachmentWriteError
from sebastian.domain.gmail import ParsedAttachment, WrittenAttachment

DEFAULT_FILENAME = "attachment"


def sanitize_filename(filename: str) -> str:
    """Reduce a mail-supplied filename to a safe basename inside the output dir.

    Drops any directory component (both separators), control characters and
    leading dots, so a hostile or malformed name cannot escape the directory.
    """
    name = filename.replace("\\", "/").rsplit("/", 1)[-1]
    name = "".join(character for character in name if character.isprintable())
    name = name.strip().strip(".")
    return name or DEFAULT_FILENAME


def write_attachments(
    attachments: Sequence[ParsedAttachment],
    out_dir: str | Path,
    force: bool,
    fetch: Callable[[str], bytes],
) -> list[WrittenAttachment]:
    """Write a mail's attachments into ``out_dir``.

    Content is taken from the message when the part carried it inline, otherwise
    fetched with ``fetch`` in this same run (Gmail's attachment ids are
    short-lived). Collisions with existing files are refused unless ``force``.
    """
    directory = Path(out_dir)
    if not directory.is_dir():
        raise AttachmentWriteError(f"output directory does not exist: {directory}")

    targets = _plan_targets(attachments, directory)
    existing = [str(target) for target, _ in targets if target.exists()]
    if existing and not force:
        raise AttachmentWriteError(
            "refusing to overwrite existing files: "
            + ", ".join(existing)
            + " (pass --force to overwrite)"
        )

    written: list[WrittenAttachment] = []
    for target, attachment in targets:
        content = _content_of(attachment, fetch)
        try:
            target.write_bytes(content)
        except OSError as error:
            raise AttachmentWriteError(f"could not write {target}: {error}") from error
        written.append(WrittenAttachment(path=str(target), size=len(content)))
    return written


def _plan_targets(
    attachments: Sequence[ParsedAttachment], directory: Path
) -> list[tuple[Path, ParsedAttachment]]:
    used: set[str] = set()
    targets: list[tuple[Path, ParsedAttachment]] = []
    for attachment in attachments:
        name = _unique_name(sanitize_filename(attachment.filename), used)
        used.add(name)
        targets.append((directory / name, attachment))
    return targets


def _unique_name(name: str, used: set[str]) -> str:
    if name not in used:
        return name
    stem, extension = os.path.splitext(name)
    counter = 2
    while f"{stem}-{counter}{extension}" in used:
        counter += 1
    return f"{stem}-{counter}{extension}"


def _content_of(attachment: ParsedAttachment, fetch: Callable[[str], bytes]) -> bytes:
    if attachment.inline_data is not None:
        return attachment.inline_data
    if attachment.attachment_id is None:
        raise AttachmentWriteError(
            f"attachment has no downloadable content: {attachment.filename}"
        )
    return fetch(attachment.attachment_id)
