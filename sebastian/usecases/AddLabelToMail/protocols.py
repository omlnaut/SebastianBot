from typing import Protocol

from sebastian.domain.gmail import GmailLabel


class GmailClient(Protocol):
    def modify_labels(
        self,
        email_id: str,
        add_labels: list[GmailLabel] | None = None,
        remove_labels: list[GmailLabel] | None = None,
    ): ...
