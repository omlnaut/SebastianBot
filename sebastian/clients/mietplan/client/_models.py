from datetime import datetime
from pydantic import BaseModel


class MietplanFile(BaseModel):
    creation_date: datetime
    download_path: str
    filename: str


class MietplanFolder(BaseModel):
    name: str
    folder_id: str
    has_subfolders: bool
