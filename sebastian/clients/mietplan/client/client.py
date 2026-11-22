from typing import Generator

from sebastian.clients.shared.retry_session import create_retry_session
from sebastian.domain.mietplan import (
    MietplanFolder,
    MietplanWalk,
    WrittenMietplanFile,
)

from ..credentials import MietplanCredentials
from ..download import download_to_dir
from . import _download_file, _login, _verify_session, _walk_from_top_folder


class MietplanClient:
    _MAIN_FOLDER_ID = "ac4do35ktgfi79j8ids35om8udm"

    def __init__(self, credentials: MietplanCredentials):
        self._session = create_retry_session()

        _login.login(self._session, credentials.username, credentials.password)
        _verify_session.verify_session(self._session, self._MAIN_FOLDER_ID)

    def walk_from_top_folder(self) -> Generator[MietplanFolder, None, None]:
        """Walk the whole tree, raising on the first folder that cannot be read."""
        yield from _walk_from_top_folder.walk_from_top_folder(
            self._session, self._MAIN_FOLDER_ID
        )

    def walk_tolerant(self) -> MietplanWalk:
        """Walk the whole tree, reporting unreadable folders as warnings instead."""
        return _walk_from_top_folder.walk_tolerant(
            self._session, self._MAIN_FOLDER_ID
        )

    def download_file(self, download_path: str) -> bytes:
        return _download_file.download_file_to_ram(self._session, download_path)

    def download(
        self, path: str, out_dir: str, force: bool
    ) -> WrittenMietplanFile:
        """Re-walk the portal, resolve the path, and write the file below ``out_dir``."""
        return download_to_dir(
            path, out_dir, force, self.walk_tolerant, self.download_file
        )
