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


class MietplanWalkWarning(BaseModel):
    """A folder the tolerant walk could not read, and why."""

    folder_id: str
    path: list[str]
    error: str


class MietplanWalk(BaseModel):
    """One tolerant walk: the folders that were read plus the failures recorded."""

    folders: list[MietplanFolder]
    warnings: list[MietplanWalkWarning]
