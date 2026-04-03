from dataclasses import dataclass, field
import logging
from typing import Protocol

from sebastian.domain.gmail import GmailLabel
from sebastian.protocols.models import BaseActorEvent
from sebastian.usecases.usecase_handler import UseCaseHandler


class GmailClient(Protocol):
    def modify_labels(
        self,
        email_id: str,
        add_labels: list[GmailLabel] | None = None,
        remove_labels: list[GmailLabel] | None = None,
    ) -> None: ...


@dataclass
class Request:
    email_id: str
    add_labels: list[GmailLabel] = field(default_factory=list[GmailLabel])
    remove_labels: list[GmailLabel] = field(default_factory=list[GmailLabel])


class Handler(UseCaseHandler[Request]):
    def __init__(self, gmail_client: GmailClient):
        self._gmail_client = gmail_client

    def handle(self, request: Request) -> list[BaseActorEvent]:
        _log_operation(request.email_id, request.add_labels, request.remove_labels)

        self._gmail_client.modify_labels(
            request.email_id,
            add_labels=request.add_labels,
            remove_labels=request.remove_labels,
        )

        logging.info(f"Successfully modified labels for email {request.email_id}")
        return []


def _log_operation(
    email_id: str,
    add_labels: list[GmailLabel] | None,
    remove_labels: list[GmailLabel] | None,
):
    operations: list[str] = []
    if add_labels:
        operations.append(f"adding {', '.join(label.name for label in add_labels)}")
    if remove_labels:
        operations.append(
            f"removing {', '.join(label.name for label in remove_labels)}"
        )
    log_msg = f"Modifying labels for email {email_id}: {'; '.join(operations)}"
    logging.info(log_msg)
