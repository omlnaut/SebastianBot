from datetime import datetime

from pydantic import BaseModel


class MietplanFile(BaseModel):
    creation_date: datetime
    name: str
    url: str


class MietplanFolder(BaseModel):
    id: str
    path: list[str]
    files: list[MietplanFile]
