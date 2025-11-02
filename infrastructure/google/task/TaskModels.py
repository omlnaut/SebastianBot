from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, List, Optional


@dataclass
class TaskList:
    kind: str
    id: str
    etag: str
    title: str
    updated: Optional[datetime] = None
    selfLink: Optional[str] = None


@dataclass
class Task:
    kind: str
    id: str
    etag: str
    title: str
    updated: Optional[datetime] = None
    selfLink: Optional[str] = None
    position: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None
    due: Optional[datetime] = None
    links: Optional[List[Dict[str, Any]]] = None
    webViewLink: Optional[str] = None
