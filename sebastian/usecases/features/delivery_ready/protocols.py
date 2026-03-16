from typing import Protocol

from sebastian.domain.gmail import FullMailResponse

__all__ = ["GmailClient"]


class GmailClient(Protocol):
    def fetch_mails(self, query: str) -> list[FullMailResponse]: ...
