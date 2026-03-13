# pyright: basic

import base64
from typing import Self

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from pydantic import BaseModel

from sebastian.clients.google.gmail.client.retry_decorator import retry_on_network_error
from sebastian.domain.gmail import FullMailResponse


class MessageId(BaseModel):
    id: str

    @classmethod
    def from_response(cls, response: dict) -> Self:
        return cls(id=response["id"])


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


def to_full_mail_response(response: dict) -> FullMailResponse:
    def _extract_email_body(payload: dict) -> str:
        def _decode(inner: dict) -> str:
            return base64.urlsafe_b64decode(
                inner["body"]["data"].encode("utf-8")
            ).decode("utf-8")

        if "parts" in payload:
            for part in payload["parts"]:
                if part["mimeType"] == "text/html":
                    return _decode(part)
        else:
            return _decode(payload)

        return ""

    return FullMailResponse(
        id=response["id"],
        threadId=response["threadId"],
        labelIds=response["labelIds"],
        snippet=response["snippet"],
        historyId=response["historyId"],
        internalDate=response["internalDate"],
        raw_payload=response["payload"],
        sizeEstimate=response["sizeEstimate"],
        content=_extract_email_body(response["payload"]),
    )
