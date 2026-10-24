import json
from typing import Any

from googleapiclient.errors import HttpError

# Reasons that mean "the caller is not allowed", not "the call was malformed".
_AUTH_REASONS = {"authError", "forbidden", "insufficientPermissions"}


class GmailError(Exception):
    """Base class for errors raised by the Gmail client layer."""


class GmailApiError(GmailError):
    """A Gmail API call failed."""

    def __init__(
        self,
        message: str,
        status: int | None = None,
        reason: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.reason = reason


class GmailAuthError(GmailError):
    """Gmail rejected the credentials or token refresh."""

    def __init__(
        self,
        message: str,
        status: int | None = None,
        reason: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.reason = reason


class AttachmentWriteError(GmailError):
    """An attachment could not be written to the output directory."""


def gmail_error_from_http(error: HttpError) -> GmailApiError | GmailAuthError:
    """Translate an ``HttpError`` into a typed error with a printable message.

    The raw ``repr`` embeds the request URL and Google's response dict; agents
    only need one sentence, with status and reason as separate fields.
    """
    status = _status_of(error)
    message, reason = _details_of(error)
    if _is_auth_failure(status, reason):
        return GmailAuthError(message, status, reason)
    return GmailApiError(message, status, reason)


def _is_auth_failure(status: int | None, reason: str | None) -> bool:
    """401 is an expired/revoked token; 403 only if it is about permission."""
    return status == 401 or (status == 403 and reason in _AUTH_REASONS)


def _status_of(error: HttpError) -> int | None:
    status = getattr(error.resp, "status", None)
    return status if isinstance(status, int) else None


def _details_of(error: HttpError) -> tuple[str, str | None]:
    payload = _error_payload(error.content)
    if payload is not None:
        message = payload.get("message")
        if isinstance(message, str) and message.strip():
            return message.strip(), _reason_of(payload)
    return (error.reason or "Gmail API request failed").strip(), None


def _error_payload(content: bytes) -> dict[str, Any] | None:
    try:
        body = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    if not isinstance(body, dict):
        return None
    payload = body.get("error")
    return payload if isinstance(payload, dict) else None


def _reason_of(payload: dict[str, Any]) -> str | None:
    errors = payload.get("errors")
    if isinstance(errors, list):
        for entry in errors:
            if isinstance(entry, dict) and isinstance(entry.get("reason"), str):
                return entry["reason"]
    details = payload.get("details")
    if isinstance(details, list):
        for entry in details:
            if isinstance(entry, dict) and isinstance(entry.get("reason"), str):
                return entry["reason"]
    return None
