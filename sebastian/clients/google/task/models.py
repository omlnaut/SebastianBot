from datetime import datetime

from pydantic import BaseModel


class TaskResponse(BaseModel):
    kind: str
    id: str
    etag: str
    title: str
    due: datetime
    updated: datetime | None = None
    selfLink: str | None = None
    position: str | None = None
    notes: str | None = None
    status: str | None = None
    links: list[dict[str, str]] | None = None
    webViewLink: str | None = None
