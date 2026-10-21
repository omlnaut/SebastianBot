import base64
from email.utils import getaddresses, parsedate_to_datetime

from sebastian.domain.gmail import ParsedAttachment, ParsedMail


def parse_payload(payload: dict) -> ParsedMail:
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
