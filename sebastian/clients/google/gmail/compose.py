"""Turn requested draft inputs into raw MIME, without argv or network.

The CLI parses flags, this module decides whether they can become a message, and
``GmailClient`` is the only thing that talks to the API. Keeping composition here
means the bot can reuse it later and that everything below is a pure function of
its arguments, which is also what makes ``--dry-run`` free.
"""

import base64
import mimetypes
import os
import re
from email.message import EmailMessage
from email.utils import getaddresses
from pathlib import Path
from typing import Iterable, Mapping, Sequence

from sebastian.clients.google.gmail.errors import DraftInputError, DraftIoError
from sebastian.domain.gmail import (
    ComposedDraft,
    DraftRequest,
    OutgoingAttachment,
    ReplyContext,
    ReplyTarget,
)

# Gmail's cap applies to the message *after* base64, which inflates by a third.
MAX_ENCODED_BYTES = 25 * 1024 * 1024

_ADDRESS = re.compile(r"^[^@\s,;]+@[^@\s,;]+$")
_FORBIDDEN_NAME_CHARS = frozenset("/\\") | {chr(code) for code in range(32)}


def parse_recipients(values: Sequence[str]) -> list[str]:
    """Parse recipient flags into normalized addresses, rejecting the rest."""
    for value in values:
        _reject_line_breaks(value, "recipient")
    recipients: list[str] = []
    for name, address in getaddresses(values):
        address = address.strip()
        if not _ADDRESS.match(address):
            raise DraftInputError(f"not a usable email address: {address!r}")
        recipients.append(_format_address(name, address))
    return _dedupe(recipients)


def parse_renames(values: Sequence[str]) -> dict[str, str]:
    """Parse ``<basename>=<newname>`` pairs into an order-free rename map."""
    renames: dict[str, str] = {}
    for value in values:
        base, separator, new_name = value.partition("=")
        if not separator:
            raise DraftInputError(
                f"--attach-name expects <basename>=<newname>, got {value!r}"
            )
        _validate_attachment_name(new_name)
        renames[base.strip()] = new_name
    return renames


def resolve_attachments(
    paths: Sequence[str], renames: Mapping[str, str]
) -> list[OutgoingAttachment]:
    """Read every attachment, applying the rename map and rejecting collisions."""
    basenames = [_basename_of(path) for path in paths]
    unknown = [base for base in renames if base not in basenames]
    if unknown:
        raise DraftInputError(
            "--attach-name refers to no attachment: " + ", ".join(sorted(unknown))
        )

    attachments: list[OutgoingAttachment] = []
    taken: dict[str, str] = {}
    for path, basename in zip(paths, basenames):
        filename = renames.get(basename, basename)
        key = filename.casefold()
        if key in taken:
            raise DraftInputError(
                f"two attachments would both be named {filename!r} "
                f"({taken[key]} and {path}); rename one with --attach-name"
            )
        taken[key] = path
        attachments.append(load_attachment(path, filename))
    return attachments


def load_attachment(path: str, filename: str) -> OutgoingAttachment:
    """Read one attachment from disk, classifying the failure that can happen."""
    if not os.path.exists(path):
        raise DraftInputError(f"attachment does not exist: {path}")
    if not os.path.isfile(path):
        raise DraftInputError(f"attachment is not a regular file: {path}")
    try:
        data = Path(path).read_bytes()
    except OSError as error:
        raise DraftIoError(
            f"could not read attachment {path}: {error.strerror or error}"
        ) from error
    if not data:
        raise DraftIoError(f"attachment is empty: {path}")
    mime_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
    return OutgoingAttachment(
        path=path,
        filename=filename,
        mime_type=mime_type,
        size=len(data),
        data=data,
    )


def compose_draft(request: DraftRequest) -> ComposedDraft:
    """Validate a request, render it to MIME, and enforce Gmail's size cap."""
    message = build_message(request)
    raw = message.as_bytes()
    encoded = base64.urlsafe_b64encode(raw).decode("ascii")
    if len(encoded) > MAX_ENCODED_BYTES:
        raise DraftInputError(_too_large(request, len(encoded)))
    return ComposedDraft(
        raw=raw,
        encoded=encoded,
        encoded_bytes=len(encoded),
        request=request,
    )


def build_message(request: DraftRequest) -> EmailMessage:
    """Build the MIME message for one draft; ``From`` is left to Gmail."""
    if not request.to:
        raise DraftInputError("a draft needs at least one recipient")
    _reject_line_breaks(request.subject, "subject")

    message = EmailMessage()
    message["To"] = ", ".join(request.to)
    if request.cc:
        message["Cc"] = ", ".join(request.cc)
    if request.bcc:
        message["Bcc"] = ", ".join(request.bcc)
    if request.subject:
        message["Subject"] = request.subject
    if request.in_reply_to:
        message["In-Reply-To"] = request.in_reply_to
    if request.references:
        message["References"] = request.references
    message.set_content(request.body)
    for attachment in request.attachments:
        maintype, _, subtype = attachment.mime_type.partition("/")
        message.add_attachment(
            attachment.data,
            maintype=maintype,
            subtype=subtype or "octet-stream",
            filename=attachment.filename,
        )
    return message


def derive_reply_target(
    context: ReplyContext, own_address: str | None, reply_all: bool
) -> ReplyTarget:
    """Derive recipients and threading headers for a reply draft."""
    sender = _single_address(context.sender)
    if sender is None:
        raise DraftInputError(
            f"cannot derive a reply recipient from the original sender "
            f"{context.sender!r}"
        )

    to = [sender]
    cc: list[str] = []
    if reply_all:
        own = (own_address or "").strip().casefold()
        to = _dedupe([sender, *context.to], exclude=own)
        cc = _dedupe([*context.cc], exclude=own, already=to)

    return ReplyTarget(
        to=to,
        cc=cc,
        subject=_reply_subject(context.subject),
        thread_id=context.thread_id,
        in_reply_to=context.message_id_header,
        references=_reply_references(context),
    )


_REPLY_PREFIXES = ("re:", "aw:", "wg:")


def _reply_subject(subject: str) -> str:
    """Prefix a reply subject, without doubling a prefix that is already there.

    ``aw:``/``wg:`` are the German client prefixes for the same thing; a mail
    that already carries one is a reply, and stacking ``Re:`` on it reads badly.
    """
    stripped = subject.strip()
    if stripped.casefold().startswith(_REPLY_PREFIXES):
        return stripped
    return f"Re: {stripped}"


def _reply_references(context: ReplyContext) -> str | None:
    parts = [part for part in (context.references, context.message_id_header) if part]
    return " ".join(parts) or None


def _basename_of(path: str) -> str:
    basename = os.path.basename(path.rstrip("/"))
    if not basename:
        raise DraftInputError(f"attachment path has no filename: {path!r}")
    return basename


def _validate_attachment_name(name: str) -> None:
    if not name.strip():
        raise DraftInputError("attachment name must not be empty")
    if any(char in _FORBIDDEN_NAME_CHARS for char in name):
        raise DraftInputError(
            f"attachment name {name!r} must not contain path separators or "
            "control characters"
        )


def _too_large(request: DraftRequest, encoded_bytes: int) -> str:
    files = (
        ", ".join(f"{a.filename} ({a.size} bytes)" for a in request.attachments)
        or "none"
    )
    raw_budget = MAX_ENCODED_BYTES * 3 // 4
    return (
        f"the encoded message is {encoded_bytes} bytes, over Gmail's "
        f"{MAX_ENCODED_BYTES} byte limit (base64 adds a third, so attachments "
        f"must fit in about {raw_budget} raw bytes); attachments: {files}"
    )


def _reject_line_breaks(value: str, what: str) -> None:
    if "\r" in value or "\n" in value:
        raise DraftInputError(f"{what} must not contain a line break: {value!r}")


def _format_address(name: str, address: str) -> str:
    name = name.strip()
    return f"{name} <{address}>" if name else address


def _address_part(formatted: str) -> str:
    parsed = getaddresses([formatted])
    return parsed[0][1] if parsed else formatted


def _single_address(value: str) -> str | None:
    parsed = [(name, address) for name, address in getaddresses([value]) if address]
    if not parsed:
        return None
    name, address = parsed[0]
    if not _ADDRESS.match(address):
        return None
    return _format_address(name, address)


def _dedupe(
    addresses: Iterable[str],
    exclude: str = "",
    already: Sequence[str] = (),
) -> list[str]:
    """Drop an address, duplicates, and anything already in ``already``."""
    seen = {_address_part(address).casefold() for address in already}
    if exclude:
        seen.add(exclude)
    unique: list[str] = []
    for address in addresses:
        key = _address_part(address).casefold()
        if key in seen:
            continue
        seen.add(key)
        unique.append(address)
    return unique
