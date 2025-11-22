import html
from datetime import datetime
from typing import Generator
import requests

from sebastian.clients.mietplan.models import File, Folder
from ._models import MietplanFile, MietplanFolder
import logging


def _get_folders(
    session: requests.Session, parent_folder_id: str
) -> list[MietplanFolder]:
    url = f"https://mietplan-dresden.de/moxanos/json?&svc=org.auctores.bvi.mietplan2&msg=getFolders&fdFolder={parent_folder_id}"
    response = session.get(url)
    response.raise_for_status()
    return [
        MietplanFolder(
            name=folder_json["filename"],
            folder_id=folder_json["fileid"],
            has_subfolders=folder_json["filechildren"],
        )
        for folder_json in response.json().values()
    ]


def _get_files(session: requests.Session, folder_id: str) -> list[MietplanFile]:
    url = f"https://mietplan-dresden.de/moxanos/json?&svc=org.auctores.bvi.mietplan2&msg=getFiles&fdFolder={folder_id}"
    response = session.get(url)
    response.raise_for_status()

    files = []
    for file_json in response.json().values():
        date_format = "%d.%m.%Y"
        creation_date = datetime.strptime(file_json["filecrea"], date_format)
        download_path = html.unescape(file_json["filepath"])
        raw_filename = download_path.split("/")[-1]
        filename = html.unescape(raw_filename)
        files.append(
            MietplanFile(
                creation_date=creation_date,
                download_path=download_path,
                filename=filename,
            )
        )
    return files


def walk_from_top_folder(
    session: requests.Session, top_folder_id: str
) -> Generator[Folder, None, None]:
    def _walk(folder_id: str, path: list[str]) -> Generator[Folder, None, None]:
        logging.info(f"Walking folder: {folder_id}, path: {'/'.join(path)}")

        # First, yield the current folder with its files
        files = [
            File(
                creation_date=f.creation_date,
                name=f.filename,
                url=f.download_path,
            )
            for f in _get_files(session, folder_id)
        ]
        logging.info(f"Found {len(files)} files in folder: {folder_id}")
        yield Folder(id=folder_id, path=path, files=files)

        # Then, recurse into subfolders
        subfolders = _get_folders(session, folder_id)
        logging.info(f"Found {len(subfolders)} subfolders in folder: {folder_id}")
        for subfolder in subfolders:
            logging.info(
                f"Processing subfolder: {subfolder.name} (ID: {subfolder.folder_id})"
            )
            yield from _walk(subfolder.folder_id, path + [subfolder.name])

    logging.info(f"Starting walk from top folder: {top_folder_id}")
    yield from _walk(top_folder_id, [])
    logging.info(f"Completed walk from top folder: {top_folder_id}")
