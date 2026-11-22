from collections.abc import Sequence
from datetime import datetime

from pydantic import BaseModel


def join_path(segments: Sequence[str]) -> str:
    """Join path segments with the portal's ``/`` separator."""
    return "/".join(segments)


def is_path_prefix(path: Sequence[str], prefix: Sequence[str]) -> bool:
    """Whether ``prefix`` matches ``path`` from its first segment.

    The match is segment-wise, so ``Archiv`` covers ``Archiv`` and
    ``Archiv/2019`` but not ``Archiv2``. An empty prefix covers every path.
    """
    return list(path[: len(prefix)]) == list(prefix)


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


class WrittenMietplanFile(BaseModel):
    """One webdepot file written to disk: its portal path, local path and size."""

    portal_path: str
    path: str
    size: int
