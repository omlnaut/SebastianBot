import base64

from pydantic import BaseModel


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
    payload: str
    sizeEstimate: int
    historyId: str
    internalDate: str

    @staticmethod
    def from_response(response: dict) -> "FullMailResponse":
        return FullMailResponse(
            id=response["id"],
            threadId=response["threadId"],
            labelIds=response["labelIds"],
            snippet=response["snippet"],
            historyId=response["historyId"],
            internalDate=response["internalDate"],
            payload=_extract_email_body(response["payload"]),
            sizeEstimate=response["sizeEstimate"],
        )
        )
