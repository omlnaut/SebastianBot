"""Look up a Drive file id by its full path inside a base folder.

This is the read half of the upsert flow: the mietplan sync asks whether the
path it is about to write already exists, and only creates when it does not.
Nothing here creates folders or files.
"""

import os
from typing import Any

from ._deterministic import pick_oldest

FOLDER_MIME_TYPE = "application/vnd.google-apps.folder"
_FOLDER_MIME_CLAUSE = f"mimeType='{FOLDER_MIME_TYPE}'"
_FILE_MIME_CLAUSE = f"mimeType!='{FOLDER_MIME_TYPE}'"
_LIST_FIELDS = "files(id, name, createdTime)"


def find_file_with_path(
    service: Any, filename_with_path: str, base_folder_id: str
) -> str | None:
    """Return the id of the file at ``filename_with_path``, or ``None``.

    ``filename_with_path`` is relative to ``base_folder_id`` and uses ``/`` as
    the separator, exactly like the path that :func:`upload_file_with_path`
    writes. A missing folder along the way means the file cannot exist.
    """
    parent_folder_id = _find_folder_path(
        service, os.path.dirname(filename_with_path), base_folder_id
    )
    if parent_folder_id is None:
        return None

    return _find_child_id(
        service,
        os.path.basename(filename_with_path),
        parent_folder_id,
        _FILE_MIME_CLAUSE,
    )


def _find_folder_path(
    service: Any, dir_path: str, base_folder_id: str
) -> str | None:
    current_folder_id = base_folder_id
    for folder_name in dir_path.split("/"):
        if not folder_name:
            continue
        found = _find_child_id(
            service, folder_name, current_folder_id, _FOLDER_MIME_CLAUSE
        )
        if found is None:
            return None
        current_folder_id = found
    return current_folder_id


def _find_child_id(
    service: Any, name: str, parent_id: str, mime_clause: str
) -> str | None:
    query = (
        f"name='{_escape_for_query(name)}' and '{parent_id}' in parents "
        f"and {mime_clause} and trashed=false"
    )
    result = service.files().list(q=query, fields=_LIST_FIELDS).execute()
    items: list[dict[str, Any]] = result.get("files", [])
    return pick_oldest(items)


def _escape_for_query(value: str) -> str:
    """Escape a Drive query string literal (backslash and single quote)."""
    return value.replace("\\", "\\\\").replace("'", "\\'")
