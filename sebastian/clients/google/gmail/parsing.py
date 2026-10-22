import base64
from datetime import datetime, timezone
from email.utils import getaddresses, parsedate_to_datetime
from typing import Any

from sebastian.domain.gmail import (
    AttachmentInfo,
    MailHit,
    ParsedAttachment,
    ParsedMail,
)


def parse_payload(payload: dict[str, Any]) -> ParsedMail:
    """Turn a raw Gmail message payload into a normalized mail model.

    Fixes, in one place, the three parsing defects a recall tool hits:
    plain text is preferred with HTML fallback available, the whole part tree
    is walked for attachments, and the full header set is parsed.
    """
    headers = _parse_headers(payload.get("headers") or [])

    return ParsedMail(
        sender=_format_single_address(headers.get("from")),
        to=_format_addresses(headers.get("to")),
        cc=_format_addresses(headers.get("cc")),
        subject=headers.get("subject", ""),
        date=_format_date(headers.get("date")),
        message_id=headers.get("message-id"),
        text_body=_find_body(payload, "text/plain"),
        html_body=_find_body(payload, "text/html"),
        attachments=_collect_attachments(payload),
    )


def _parse_headers(headers: list[dict]) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for header in headers:
        name = (header.get("name") or "").lower()
        if name:
            parsed[name] = header.get("value") or ""
    return parsed


def _walk(part: dict):
    yield part
    for child in part.get("parts") or []:
        yield from _walk(child)


def _is_body_part(part: dict) -> bool:
    body = part.get("body") or {}
    return not part.get("filename") and "attachmentId" not in body


def _find_body(payload: dict, mime_type: str) -> str | None:
    for part in _walk(payload):
        if part.get("mimeType") != mime_type or not _is_body_part(part):
            continue
        data = (part.get("body") or {}).get("data")
        if data:
            return _decode(data)
    return None


def _collect_attachments(payload: dict) -> list[ParsedAttachment]:
    attachments: list[ParsedAttachment] = []
    for part in _walk(payload):
        filename = part.get("filename")
        if not filename:
            continue
        body = part.get("body") or {}
        attachments.append(
            ParsedAttachment(
                filename=filename,
                mime_type=part.get("mimeType") or "",
                size=body.get("size") or 0,
                attachment_id=body.get("attachmentId"),
            )
        )
    return attachments


def _decode(data: str) -> str:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding).decode("utf-8", errors="replace")


def _format_single_address(value: str | None) -> str:
    addresses = _format_addresses(value)
    return addresses[0] if addresses else ""


def _format_addresses(value: str | None) -> list[str]:
    if not value:
        return []
    return [
        f"{name} <{address}>" if name else address
        for name, address in getaddresses([value])
        if address
    ]


def _format_date(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return parsedate_to_datetime(value).isoformat()
    except (TypeError, ValueError):
        return None


def normalize_hit(message: dict[str, Any], label_names: dict[str, str]) -> MailHit:
    """Turn a raw Gmail message into the shared hit shape, resolving label names."""
    parsed = parse_payload(message.get("payload") or {})
    label_ids = list(message.get("labelIds") or [])
    internal_date = message.get("internalDate") or ""

    return MailHit(
        id=message["id"],
        thread_id=message.get("threadId") or "",
        sender=parsed.sender,
        to=parsed.to,
        cc=parsed.cc,
        subject=parsed.subject,
        date=parsed.date or _date_from_internal(internal_date),
        internal_date=internal_date,
        labels=[label_names.get(label_id, label_id) for label_id in label_ids],
        label_ids=label_ids,
        snippet=message.get("snippet") or "",
        size_estimate=message.get("sizeEstimate") or 0,
        has_attachments=bool(parsed.attachments),
        attachments=[
            AttachmentInfo(
                filename=attachment.filename,
                mime_type=attachment.mime_type,
                size=attachment.size,
            )
            for attachment in parsed.attachments
        ],
    )


def _date_from_internal(internal_date: str) -> str | None:
    if not internal_date:
        return None
    try:
        return datetime.fromtimestamp(
            int(internal_date) / 1000, tz=timezone.utc
        ).isoformat()
    except (TypeError, ValueError, OverflowError, OSError):
        return None
