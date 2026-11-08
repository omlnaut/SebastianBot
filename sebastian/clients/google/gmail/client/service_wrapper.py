# pyright: basic

import base64
import re
from functools import wraps
from typing import Any, Self

from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from pydantic import BaseModel, ConfigDict, Field
from tenacity import RetryError

from sebastian.clients.google.gmail.client.retry_decorator import retry_on_network_error
from sebastian.clients.google.gmail.errors import (
    GmailApiError,
    GmailAuthError,
    gmail_error_from_http,
)
from sebastian.domain.gmail import FullMailResponse, GmailLabelResponse, PdfMessagePart


class MessageId(BaseModel):
    id: str

    @classmethod
    def from_response(cls, response: dict) -> Self:
        return cls(id=response["id"])


class MessageIdPage(BaseModel):
    ids: list[str]
    next_page_token: str | None = None
    result_size_estimate: int | None = None


def _search_fields() -> str:
    """Projection for a search hit: metadata plus the part tree, never body data."""
    leaves = ("filename", "mimeType", "body/size")
    nested = [
        f"payload/{'/'.join(['parts'] * depth)}/{leaf}"
        for depth in range(1, 5)
        for leaf in leaves
    ]
    return ",".join(
        [
            "id",
            "threadId",
            "labelIds",
            "snippet",
            "sizeEstimate",
            "internalDate",
            "payload/mimeType",
            "payload/filename",
            "payload/body/size",
            "payload/headers",
            *nested,
        ]
    )


SEARCH_FIELDS = _search_fields()

REPLY_CONTEXT_HEADERS = ["Message-Id", "References", "Subject", "From", "To", "Cc"]


def _translate_errors(function):
    """Map lower-level client exceptions onto the CLI's typed error kinds."""

    @wraps(function)
    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except RetryError as error:
            cause = error.last_attempt.exception() if error.last_attempt else error
            raise _as_gmail_error(cause) from error
        except (HttpError, RefreshError, OSError) as error:
            raise _as_gmail_error(error) from error

    return wrapper


def _as_gmail_error(error: BaseException) -> Exception:
    if isinstance(error, HttpError):
        return gmail_error_from_http(error)
    if isinstance(error, RefreshError):
        return GmailAuthError(str(error))
    return GmailApiError(str(error))


class GmailServiceWrapper:
    def __init__(self, credentials: Credentials):
        self._credentials = credentials
        self._service = build(
            "gmail", "v1", credentials=credentials, cache_discovery=False
        )

    @retry_on_network_error(max_retries=3, initial_delay=1.0, backoff_factor=2.0)
    def fetch_message_ids(self, query: str) -> list[MessageId]:
        """Fetch message IDs matching the query."""
        response = self._service.users().messages().list(userId="me", q=query).execute()
        messages = response.get("messages", [])
        ids = [msg["id"] for msg in messages]

        return [MessageId(id=id) for id in ids]

    @retry_on_network_error(max_retries=3, initial_delay=1.0, backoff_factor=2.0)
    def fetch_full_mail(self, msg_id: str) -> FullMailResponse:
        """Fetch full email message by ID"""
        message = (
            self._service.users()
            .messages()
            .get(userId="me", id=msg_id, format="full")
            .execute()
        )
        return to_full_mail_response(message)

    @retry_on_network_error(max_retries=3, initial_delay=1.0, backoff_factor=2.0)
    def download_pdf_attachment(self, message_id: str, attachment_id: str) -> bytes:
        """Download a single PDF attachment and return as BytesIO"""
        attachment = (
            self._service.users()
            .messages()
            .attachments()
            .get(
                userId="me",
                messageId=message_id,
                id=attachment_id,
            )
            .execute()
        )

        if not attachment:
            raise ValueError("Attachment not found")

        pdf_bytes = base64.urlsafe_b64decode(attachment["data"])
        return pdf_bytes

    @retry_on_network_error(max_retries=3, initial_delay=1.0, backoff_factor=2.0)
    def modify_labels(self, email_id: str, body: dict[str, list[str]]) -> None:
        self._service.users().messages().modify(
            userId="me", id=email_id, body=body
        ).execute()

    @retry_on_network_error(max_retries=3, initial_delay=1.0, backoff_factor=2.0)
    def fetch_labels(self) -> list[GmailLabelResponse]:
        """Fetch all available Gmail labels for the authenticated user."""
        response = self._service.users().labels().list(userId="me").execute()
        labels = response.get("labels", [])
        return [GmailLabelResponse.model_validate(label) for label in labels]

    @_translate_errors
    @retry_on_network_error(max_retries=3, initial_delay=1.0, backoff_factor=2.0)
    def list_message_ids(
        self, query: str, max_results: int, page_token: str | None = None
    ) -> MessageIdPage:
        """List one page of message ids for a raw Gmail query."""
        response = (
            self._service.users()
            .messages()
            .list(
                userId="me",
                q=query,
                maxResults=max_results,
                pageToken=page_token,
            )
            .execute()
        )
        return MessageIdPage(
            ids=[message["id"] for message in response.get("messages", [])],
            next_page_token=response.get("nextPageToken"),
            result_size_estimate=response.get("resultSizeEstimate"),
        )

    @_translate_errors
    @retry_on_network_error(max_retries=3, initial_delay=1.0, backoff_factor=2.0)
    def fetch_search_message(self, msg_id: str) -> dict[str, Any]:
        """Fetch a search hit: metadata and part tree, but no body bytes."""
        return (
            self._service.users()
            .messages()
            .get(userId="me", id=msg_id, format="full", fields=SEARCH_FIELDS)
            .execute()
        )

    @_translate_errors
    @retry_on_network_error(max_retries=3, initial_delay=1.0, backoff_factor=2.0)
    def fetch_full_message(self, msg_id: str) -> dict[str, Any]:
        """Fetch one whole message, body bytes included."""
        return (
            self._service.users()
            .messages()
            .get(userId="me", id=msg_id, format="full")
            .execute()
        )

    @_translate_errors
    @retry_on_network_error(max_retries=3, initial_delay=1.0, backoff_factor=2.0)
    def fetch_attachment(self, message_id: str, attachment_id: str) -> bytes:
        """Download one attachment's content."""
        attachment = (
            self._service.users()
            .messages()
            .attachments()
            .get(userId="me", messageId=message_id, id=attachment_id)
            .execute()
        )
        data = attachment.get("data") or ""
        return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))

    @_translate_errors
    @retry_on_network_error(max_retries=3, initial_delay=1.0, backoff_factor=2.0)
    def list_labels(self) -> list[GmailLabelResponse]:
        """Fetch labels, with client errors mapped to typed Gmail errors."""
        response = self._service.users().labels().list(userId="me").execute()
        return [
            GmailLabelResponse.model_validate(label)
            for label in response.get("labels", [])
        ]

    @_translate_errors
    @retry_on_network_error(max_retries=3, initial_delay=1.0, backoff_factor=2.0)
    def create_draft(self, message: dict[str, Any]) -> dict[str, Any]:
        """Create one draft from an already encoded raw message."""
        return (
            self._service.users()
            .drafts()
            .create(userId="me", body={"message": message})
            .execute()
        )

    @_translate_errors
    @retry_on_network_error(max_retries=3, initial_delay=1.0, backoff_factor=2.0)
    def fetch_reply_context(self, msg_id: str) -> dict[str, Any]:
        """Fetch only the headers a reply draft is derived from."""
        return (
            self._service.users()
            .messages()
            .get(
                userId="me",
                id=msg_id,
                format="metadata",
                metadataHeaders=REPLY_CONTEXT_HEADERS,
            )
            .execute()
        )

    @_translate_errors
    @retry_on_network_error(max_retries=3, initial_delay=1.0, backoff_factor=2.0)
    def fetch_profile_address(self) -> str:
        """The authenticated account's own address, used to exclude it on reply-all."""
        profile = self._service.users().getProfile(userId="me").execute()
        return str(profile.get("emailAddress") or "")


def to_full_mail_response(response: dict) -> FullMailResponse:
    def _extract_email_body(payload: dict) -> str:
        def _decode(inner: dict) -> str:
            return base64.urlsafe_b64decode(
                inner["body"]["data"].encode("utf-8")
            ).decode("utf-8")

        if "parts" in payload:
            for part in payload["parts"]:
                if (
                    part["mimeType"] == "text/html"
                    and "body" in part
                    and "data" in part["body"]
                ):
                    return _decode(part)
        else:
            return _decode(payload)

        return ""

    def _extract_pdf_parts(payload: dict) -> list[PdfMessagePart]:
        """Extract PDF attachment parts from a message"""
        if "parts" not in payload:
            return []

        parts = payload["parts"]
        pdf_parts = [
            part for part in parts if part.get("mimeType") == "application/pdf"
        ]
        return [PdfMessagePart.model_validate(part) for part in pdf_parts]

    def _extract_subject(payload: dict) -> str:
        """Extract the Subject header from the message payload."""
        headers = payload.get("headers", [])
        for header in headers:
            if header.get("name", "").lower() == "subject":
                return header.get("value", "")
        return ""

    def _extract_from_email(payload: dict) -> str:
        """Extract normalized sender email from the From header value."""
        headers = payload.get("headers", [])
        for header in headers:
            if header.get("name", "").lower() != "from":
                continue

            header_value = header.get("value", "")
            match = re.search(r"<([^>]+)>", header_value)
            if match:
                return match.group(1).strip()
            return header_value.strip()

        return ""

    return FullMailResponse(
        id=response["id"],
        threadId=response["threadId"],
        labelIds=response["labelIds"],
        is_read="UNREAD" not in response["labelIds"],
        subject=_extract_subject(response["payload"]),
        from_email=_extract_from_email(response["payload"]),
        snippet=response["snippet"],
        historyId=response["historyId"],
        internalDate=response["internalDate"],
        sizeEstimate=response["sizeEstimate"],
        content=_extract_email_body(response["payload"]),
        pdf_parts=_extract_pdf_parts(response["payload"]),
    )
