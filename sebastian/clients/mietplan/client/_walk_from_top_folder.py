import html
import logging
from datetime import datetime
from typing import Generator

import requests

from sebastian.domain.mietplan import MietplanFile, MietplanFolder

from ._models import MietplanFile as MietplanRawFile
from ._models import MietplanFolder as MietplanRawFolder

REQUEST_TIMEOUT_SECONDS = (10, 90)


def _get_folders(
    session: requests.Session, parent_folder_id: str
) -> list[MietplanRawFolder]:
    url = f"https://mietplan-dresden.de/moxanos/json?&svc=org.auctores.bvi.mietplan2&msg=getFolders&fdFolder={parent_folder_id}"
    response = session.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
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
    url = f"https://mietplan-dresden.de/moxanos/json?&svc=org.auctores.bvi.mietplan2&msg=getFiles&fdFolder={folder_id}"
    response = session.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
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


def walk_from_top_folder(
    session: requests.Session, top_folder_id: str
) -> Generator[MietplanFolder, None, None]:
    def _walk(folder_id: str, path: list[str]) -> Generator[MietplanFolder, None, None]:
        logging.debug(f"Walking folder: {folder_id}, path: {'/'.join(path)}")

        # First, yield the current folder with its files
        try:
            files = [
                MietplanFile(
                    creation_date=f.creation_date,
                    name=f.filename,
                    url=f.download_path,
                )
                for f in _get_files(session, folder_id)
            ]
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
