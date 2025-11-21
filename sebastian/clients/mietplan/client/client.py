from io import BytesIO
from typing import Generator
import requests

from ..credentials import MietplanCredentials
from sebastian.clients.mietplan.models import Folder
from . import _login, _walk, _download


class MietplanClient:
    _MAIN_FOLDER_ID = "ac4do35ktgfi79j8ids35om8udm"

    def __init__(self, credentials: MietplanCredentials):
        self.credentials = credentials
        self.session = requests.Session()
        _login.login(self.session, self.credentials.username, self.credentials.password)

    def walk_from_top_folder(self) -> Generator[Folder, None, None]:
        yield from _walk.walk_from_top_folder(self.session, self._MAIN_FOLDER_ID)

    def download_file(self, download_path: str) -> BytesIO:
        return _download.download_file_to_ram(self.session, download_path)
