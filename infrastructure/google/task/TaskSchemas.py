from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class CreateTaskEvent(BaseModel):
    title: str
    notes: Optional[str] = None
    due: Optional[datetime] = None
