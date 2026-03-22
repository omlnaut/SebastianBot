import requests

from sebastian.clients.bibo.client import _parse_account_page
from sebastian.usecases.features.bibo_lending_sync.protocols import BookLendingInfo

from ..credentials import BiboCredentials
from . import _login

_BASE_URL = "https://katalog.bibo-dresden.de/webOPACClient"


class BiboClient:
    def __init__(self, credentials: BiboCredentials):
        self._session = requests.Session()
        self._login(credentials)

    def _login(self, credentials: BiboCredentials) -> None:
        _login.login(self._session, credentials.username, credentials.password)

    def _fetch_account_page(self) -> str:
        response = self._session.get(
            f"{_BASE_URL}/userAccount.do",
            params={"methodToCall": "show", "type": "1"},
        )
        response.raise_for_status()
        return response.text

    def fetch_open_lendings(self) -> list[BookLendingInfo]:
        html = self._fetch_account_page()
        return _parse_account_page.parse_account_page(html)
