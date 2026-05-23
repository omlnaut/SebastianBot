from sebastian.clients.bibo.client import _parse_account_page
from sebastian.clients.shared.retry_session import create_retry_session
from sebastian.domain.bibo import Lending

from ..credentials import BiboAccountCredentials
from . import _login

_BASE_URL = "https://katalog.bibo-dresden.de/webOPACClient"


class BiboClient:
    def __init__(self, credentials: BiboAccountCredentials):
        self._session = create_retry_session(total_retries=5)
        self._login(credentials)

    def _login(self, credentials: BiboAccountCredentials) -> None:
        _login.login(self._session, credentials.username, credentials.password)

    def _fetch_account_page(self) -> str:
        response = self._session.get(
            f"{_BASE_URL}/userAccount.do",
            params={"methodToCall": "show", "type": "1"},
        )
        response.raise_for_status()
        return response.text

    def fetch_open_lendings(self) -> list[Lending]:
        html = self._fetch_account_page()
        return _parse_account_page.parse_account_page(html)
