from typing import Protocol

from sebastian.domain.gmail import FullMailResponse


class GmailClient(Protocol):
    def fetch_mails(self, query: str) -> list[FullMailResponse]: ...
