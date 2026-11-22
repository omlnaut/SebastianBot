"""Replace the *content* of an existing Drive file, in place.

``files().update`` with only ``media_body`` and ``fields="id"`` and no metadata
body: the file keeps its id, its parents and its sharing. Renaming or
re-parenting is deliberately not possible through this function -- the sync
only ever wants new bytes at the same path (spec V3, decision D12).
"""

from io import BytesIO
from typing import Any

from googleapiclient.http import MediaIoBaseUpload


def replace_file_content(
    service: Any, file_id: str, content: bytes, mime_type: str
) -> None:
    """Write ``content`` into the file ``file_id``, keeping everything else."""
    media = MediaIoBaseUpload(BytesIO(content), mimetype=mime_type, resumable=True)

    service.files().update(fileId=file_id, media_body=media, fields="id").execute()
