from typing import Generator

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from sebastian.domain.mietplan import MietplanFolder

from ..credentials import MietplanCredentials
from . import _download_file, _login, _walk_from_top_folder


class MietplanClient:
    _MAIN_FOLDER_ID = "ac4do35ktgfi79j8ids35om8udm"

    def __init__(self, credentials: MietplanCredentials):
        self._session = requests.Session()
        retry = Retry(
            total=5,
            connect=5,
            read=5,
            status=5,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=frozenset({"GET", "POST"}),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        self._session.mount("https://", adapter)
        self._session.mount("http://", adapter)

        # Keep a browser-like agent for subsequent authenticated calls as well.
        self._session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/132.0.0.0 Safari/537.36"
                )
            }
        )

        _login.login(self._session, credentials.username, credentials.password)

    def walk_from_top_folder(self) -> Generator[MietplanFolder, None, None]:
        yield from _walk_from_top_folder.walk_from_top_folder(
            self._session, self._MAIN_FOLDER_ID
        )

    def download_file(self, download_path: str) -> bytes:
        return _download_file.download_file_to_ram(self._session, download_path)
