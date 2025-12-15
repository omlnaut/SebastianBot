import base64
from dataclasses import dataclass
from io import BytesIO

from pydantic import BaseModel


@dataclass
class PdfAttachment:
    """Represents a PDF attachment with filename and data"""

    filename: str
    data: bytes


class MessageId(BaseModel):
    id: str
    thread_id: str

    @staticmethod
    def from_response(response: dict) -> "MessageId":
        return MessageId(id=response["id"], thread_id=response["threadId"])


def _extract_email_body(payload: dict) -> str:
    def _decode(inner: dict) -> str:
        return base64.urlsafe_b64decode(inner["body"]["data"].encode("utf-8")).decode(
            "utf-8"
        )

    if "parts" in payload:
        for part in payload["parts"]:
            if part["mimeType"] == "text/html":
                return _decode(part)
    else:
        return _decode(payload)

    return ""


class FullMailResponse(BaseModel):
    id: str
    threadId: str
    labelIds: list[str]
    snippet: str
    raw_payload: dict
    sizeEstimate: int
    historyId: str
    internalDate: str

    @property
    def payload(self) -> str:
        return _extract_email_body(self.raw_payload)

    @staticmethod
    def from_response(response: dict) -> "FullMailResponse":
        return FullMailResponse(
            id=response["id"],
            threadId=response["threadId"],
            labelIds=response["labelIds"],
            snippet=response["snippet"],
            historyId=response["historyId"],
            internalDate=response["internalDate"],
            raw_payload=response["payload"],
            sizeEstimate=response["sizeEstimate"],
        )
