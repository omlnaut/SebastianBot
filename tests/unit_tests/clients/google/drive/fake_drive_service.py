"""A small in-memory stand-in for the Google Drive ``files()`` resource.

Only the operations the client uses are modelled: ``list`` (a subset of the
query language), ``create`` and ``update``. Media bytes are kept on the request
object so tests can assert what would have been written.
"""

import re
from typing import Any, cast

from googleapiclient.http import MediaIoBaseUpload

FOLDER_MIME_TYPE = "application/vnd.google-apps.folder"
FILE_MIME_TYPE = "application/octet-stream"

_NAME_CLAUSE = re.compile(r"name='((?:\\.|[^'\\])*)'")
_PARENT_CLAUSE = re.compile(r"'([^']+)' in parents")
_FOLDER_ONLY_CLAUSE = "mimeType='application/vnd.google-apps.folder'"
_NOT_FOLDER_CLAUSE = "mimeType!='application/vnd.google-apps.folder'"


def folder(
    name: str,
    folder_id: str,
    parent_id: str = "base-folder-id",
    created_time: str = "2024-01-01T00:00:00.000Z",
) -> dict[str, Any]:
    return {
        "id": folder_id,
        "name": name,
        "mimeType": FOLDER_MIME_TYPE,
        "parents": [parent_id],
        "createdTime": created_time,
        "trashed": False,
    }


def file(
    name: str,
    file_id: str,
    parent_id: str = "base-folder-id",
    created_time: str = "2024-01-01T00:00:00.000Z",
    mime_type: str = FILE_MIME_TYPE,
) -> dict[str, Any]:
    return {
        "id": file_id,
        "name": name,
        "mimeType": mime_type,
        "parents": [parent_id],
        "createdTime": created_time,
        "trashed": False,
    }


def media_bytes(media: Any) -> bytes:
    """Read back everything a ``MediaIoBaseUpload`` would send."""
    length = media.size()
    return cast(bytes, media.getbytes(0, length))


def _unescape(value: str) -> str:
    return value.replace("\\'", "'").replace("\\\\", "\\")


def _matches(item: dict[str, Any], query: str) -> bool:
    if item.get("trashed"):
        return False
    name = _NAME_CLAUSE.search(query)
    if name is not None and item["name"] != _unescape(name.group(1)):
        return False
    parent = _PARENT_CLAUSE.search(query)
    if parent is not None and parent.group(1) not in item.get("parents", []):
        return False
    if _FOLDER_ONLY_CLAUSE in query and item["mimeType"] != FOLDER_MIME_TYPE:
        return False
    if _NOT_FOLDER_CLAUSE in query and item["mimeType"] == FOLDER_MIME_TYPE:
        return False
    return True


class _FakeRequest:
    def __init__(self, result: Any) -> None:
        self._result = result

    def execute(self) -> Any:
        return self._result


class _FakeFilesResource:
    def __init__(self, service: "FakeDriveService") -> None:
        self._service = service

    def list(
        self, q: str = "", fields: str = "", orderBy: str = ""
    ) -> _FakeRequest:
        self._service.list_calls.append({"q": q, "fields": fields, "orderBy": orderBy})
        matches = [item for item in self._service.items if _matches(item, q)]
        return _FakeRequest({"files": [dict(item) for item in matches]})

    def create(
        self,
        body: dict[str, Any] | None = None,
        media_body: Any = None,
        fields: str = "",
    ) -> _FakeRequest:
        self._service.create_calls.append(
            {"body": body, "media_body": media_body, "fields": fields}
        )
        self._service._next_id += 1
        new_id = f"created-{self._service._next_id}"
        if body is not None:
            self._service.items.append(
                {
                    "id": new_id,
                    "name": body["name"],
                    "mimeType": body.get("mimeType", FILE_MIME_TYPE),
                    "parents": body.get("parents", []),
                    "createdTime": "2099-01-01T00:00:00.000Z",
                    "trashed": False,
                }
            )
        return _FakeRequest({"id": new_id})

    def update(
        self,
        fileId: str = "",
        body: dict[str, Any] | None = None,
        media_body: Any = None,
        fields: str = "",
    ) -> _FakeRequest:
        self._service.update_calls.append(
            {
                "fileId": fileId,
                "body": body,
                "media_body": media_body,
                "fields": fields,
            }
        )
        return _FakeRequest({"id": fileId})


class FakeDriveService:
    def __init__(self, items: list[dict[str, Any]] | None = None) -> None:
        self.items = list(items or [])
        self.list_calls: list[dict[str, Any]] = []
        self.create_calls: list[dict[str, Any]] = []
        self.update_calls: list[dict[str, Any]] = []
        self._next_id = 0

    def files(self) -> _FakeFilesResource:
        return _FakeFilesResource(self)
