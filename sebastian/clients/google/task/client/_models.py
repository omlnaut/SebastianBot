from pydantic import BaseModel
from datetime import datetime


class TaskList(BaseModel):
    kind: str
    id: str
    etag: str
    title: str
    updated: datetime | None = None
    selfLink: str | None = None


class TaskResponse(BaseModel):
    kind: str
    id: str
    etag: str
    title: str
    due: datetime | None = None
    updated: datetime | None = None
    selfLink: str | None = None
    position: str | None = None
    notes: str | None = None
    status: str | None = None
    links: list[dict[str, str]] | None = None
    webViewLink: str | None = None
