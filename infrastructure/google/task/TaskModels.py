from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, List, Optional
from pydantic import BaseModel


@dataclass
class TaskList:
    kind: str
    id: str
    etag: str
    title: str
    updated: Optional[datetime] = None
    selfLink: Optional[str] = None


class Task(BaseModel):
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
