import html
import logging
from datetime import datetime
from typing import Generator, Sequence

import requests

from sebastian.domain.mietplan import (
    MietplanFile,
    MietplanFolder,
    MietplanWalk,
    MietplanWalkWarning,
)

from ._models import MietplanFile as MietplanRawFile
from ._models import MietplanFolder as MietplanRawFolder

REQUEST_TIMEOUT_SECONDS = (10, 90)

# A folder read fails either because the request failed or because the answer was
# not the expected JSON (an expired session answers with HTML, see
# docs/specs/mietplan-verification.md, V1).
_READ_ERRORS = (requests.RequestException, ValueError)


def folders_url(parent_folder_id: str) -> str:
    return f"https://mietplan-dresden.de/moxanos/json?&svc=org.auctores.bvi.mietplan2&msg=getFolders&fdFolder={parent_folder_id}"


def files_url(folder_id: str) -> str:
    return f"https://mietplan-dresden.de/moxanos/json?&svc=org.auctores.bvi.mietplan2&msg=getFiles&fdFolder={folder_id}"


def _get_folders(
    session: requests.Session, parent_folder_id: str
) -> list[MietplanRawFolder]:
    response = session.get(folders_url(parent_folder_id), timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    return [
        MietplanRawFolder(
            name=folder_json["filename"],
            folder_id=folder_json["fileid"],
            has_subfolders=folder_json["filechildren"],
        )
        for folder_json in response.json().values()
    ]


def _get_files(session: requests.Session, folder_id: str) -> list[MietplanRawFile]:
    response = session.get(files_url(folder_id), timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()

    def json_to_mietplan_file(file_json: dict[str, str]) -> MietplanRawFile:
        date_format = "%d.%m.%Y"
        creation_date = datetime.strptime(file_json["filecrea"], date_format)
        download_path = html.unescape(file_json["filepath"])
        raw_filename = download_path.split("/")[-1]
        filename = html.unescape(raw_filename)
        return MietplanRawFile(
            creation_date=creation_date,
            download_path=download_path,
            filename=filename,
        )

    files = [json_to_mietplan_file(file_json) for file_json in response.json().values()]
    return files


def _to_domain_files(raw_files: Sequence[MietplanRawFile]) -> list[MietplanFile]:
    return [
        MietplanFile(
            creation_date=f.creation_date,
            name=f.filename,
            url=f.download_path,
        )
        for f in raw_files
    ]


def walk_from_top_folder(
    session: requests.Session, top_folder_id: str
) -> Generator[MietplanFolder, None, None]:
    """Walk the tree strictly: the first failing folder raises."""

    def _walk(folder_id: str, path: list[str]) -> Generator[MietplanFolder, None, None]:
        logging.debug(f"Walking folder: {folder_id}, path: {'/'.join(path)}")

        # First, yield the current folder with its files
        try:
            files = _to_domain_files(_get_files(session, folder_id))
        except requests.RequestException:
            logging.exception(
                f"Failed to fetch files for folder_id={folder_id}, path={'/'.join(path)}"
            )
            raise
        logging.debug(f"Found {len(files)} files in folder: {folder_id}")
        yield MietplanFolder(id=folder_id, path=path, files=files)

        # Then, recurse into subfolders
        try:
            subfolders = _get_folders(session, folder_id)
        except requests.RequestException:
            logging.exception(
                f"Failed to fetch subfolders for folder_id={folder_id}, path={'/'.join(path)}"
            )
            raise
        logging.debug(f"Found {len(subfolders)} subfolders in folder: {folder_id}")
        for subfolder in subfolders:
            logging.debug(
                f"Processing subfolder: {subfolder.name} (ID: {subfolder.folder_id})"
            )
            yield from _walk(subfolder.folder_id, path + [subfolder.name])

    logging.info(f"Starting walk from top folder: {top_folder_id}")
    yield from _walk(top_folder_id, [])
    logging.info(f"Completed walk from top folder: {top_folder_id}")


def walk_tolerant(session: requests.Session, top_folder_id: str) -> MietplanWalk:
    """Walk the tree tolerantly: an unreadable folder becomes a warning.

    The walk still visits everything it can reach; a folder whose file list cannot
    be read is left out of `folders` (so it is not counted as scanned) and its
    subfolders are still walked. A folder whose subfolder list cannot be read is
    reported and its subtree is skipped, because it cannot be discovered.
    """
    folders: list[MietplanFolder] = []
    warnings: list[MietplanWalkWarning] = []

    def _walk(folder_id: str, path: list[str]) -> None:
        logging.debug(f"Walking folder: {folder_id}, path: {'/'.join(path)}")

        try:
            files = _to_domain_files(_get_files(session, folder_id))
        except _READ_ERRORS as error:
            logging.exception(
                f"Failed to fetch files for folder_id={folder_id}, path={'/'.join(path)}"
            )
            warnings.append(
                MietplanWalkWarning(
                    folder_id=folder_id, path=path, error=_describe(error)
                )
            )
        else:
            folders.append(MietplanFolder(id=folder_id, path=path, files=files))

        try:
            subfolders = _get_folders(session, folder_id)
        except _READ_ERRORS as error:
            logging.exception(
                f"Failed to fetch subfolders for folder_id={folder_id}, path={'/'.join(path)}"
            )
            warnings.append(
                MietplanWalkWarning(
                    folder_id=folder_id, path=path, error=_describe(error)
                )
            )
            return
        for subfolder in subfolders:
            _walk(subfolder.folder_id, path + [subfolder.name])

    logging.info(f"Starting tolerant walk from top folder: {top_folder_id}")
    _walk(top_folder_id, [])
    logging.info(
        f"Completed tolerant walk from top folder: {top_folder_id} "
        f"({len(folders)} folders, {len(warnings)} warnings)"
    )
    return MietplanWalk(folders=folders, warnings=warnings)


def _describe(error: Exception) -> str:
    """A printable reason; requests exceptions are often message-less."""
    return str(error) or error.__class__.__name__
