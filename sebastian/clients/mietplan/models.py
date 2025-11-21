from datetime import datetime
from pydantic import BaseModel


class File(BaseModel):
    creation_date: datetime
    name: str
    url: str


class Folder(BaseModel):
    id: str
    path: list[str]
    files: list[File]
