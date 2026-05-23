from typing import Generator

from sebastian.clients.shared.retry_session import create_retry_session
from sebastian.domain.mietplan import MietplanFolder

from ..credentials import MietplanCredentials
from . import _download_file, _login, _walk_from_top_folder


class MietplanClient:
    _MAIN_FOLDER_ID = "ac4do35ktgfi79j8ids35om8udm"

    def __init__(self, credentials: MietplanCredentials):
        self._session = create_retry_session()

        _login.login(self._session, credentials.username, credentials.password)

    def walk_from_top_folder(self) -> Generator[MietplanFolder, None, None]:
        yield from _walk_from_top_folder.walk_from_top_folder(
            self._session, self._MAIN_FOLDER_ID
        )

    def download_file(self, download_path: str) -> bytes:
        return _download_file.download_file_to_ram(self._session, download_path)
