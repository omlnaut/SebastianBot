from typing import Protocol, Sequence

from sebastian.domain.gmail import FullMailResponse
from sebastian.domain.side_effect import SideEffect

__all__ = ["GmailClient", "MailSubUseCase"]


class GmailClient(Protocol):
    def fetch_mails(self, query: str) -> list[FullMailResponse]: ...


class MailSubUseCase(Protocol):
    def check_if_mail_matches(self, mail: FullMailResponse) -> bool: ...

    def handle_mail(self, mail: FullMailResponse) -> Sequence[SideEffect]: ...
