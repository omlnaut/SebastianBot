from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum
from pydantic import BaseModel


@dataclass
class TaskList:
    kind: str
    id: str
    etag: str
    title: str
    updated: Optional[datetime] = None
    selfLink: Optional[str] = None


class TaskListIds(Enum):
    Default = "MDY0Mzc2NjgyMDc4MTc0Nzg3Mjk6MDow"


class TaskResponse(BaseModel):
    kind: str
    id: str
    etag: str
    title: str
    due: datetime
    updated: Optional[datetime] = None
    selfLink: Optional[str] = None
    position: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None
    links: Optional[List[Dict[str, Any]]] = None
    webViewLink: Optional[str] = None


@dataclass
class CreatedTask:
    title: str
    due: datetime
    notes: str | None
    tasklist: TaskListIds
