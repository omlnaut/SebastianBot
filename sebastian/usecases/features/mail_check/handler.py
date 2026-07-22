import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Sequence

from sebastian.domain.gmail import GmailLabel, FullMailResponse
from sebastian.domain.side_effect import ModifyMailLabel, SideEffect
from sebastian.usecases.shared.query_builder import GmailQueryBuilder
from sebastian.usecases.usecase_handler import UseCaseHandler

from .protocols import GmailClient, MailSubUseCase

__all__ = ["Request", "Handler", "GmailClient", "MailSubUseCase"]


@dataclass
class Request:
    cutoff_date: datetime


class Handler(UseCaseHandler[Request]):
    def __init__(
        self,
        gmail_client: GmailClient,
        sub_usecases: Sequence[MailSubUseCase],
    ):
        self._gmail_client = gmail_client
        self._sub_usecases = tuple(sub_usecases)

    def handle(self, request: Request) -> Sequence[SideEffect]:
        mails = self._fetch_mails_after_cutoff(request.cutoff_date)
        unprocessed_mails = self._extract_unprocessed_mails(mails)

        effects = self._process_mails(unprocessed_mails)

        return effects

    def _process_mails(
        self, unprocessed_mails: list[FullMailResponse]
    ) -> list[SideEffect]:
        effects: list[SideEffect] = []
        for mail in unprocessed_mails:
            has_match = False
            for sub_usecase in self._sub_usecases:
                if not sub_usecase.check_if_mail_matches(mail):
                    continue

                has_match = True
                effects.extend(sub_usecase.handle_mail(mail))

            if not has_match:
                effects.append(ModifyMailLabel.MarkAsProcessed(mail.id))
        return effects

    def _extract_unprocessed_mails(
        self, mails: list[FullMailResponse]
    ) -> list[FullMailResponse]:
        unprocessed_mails = [
            mail for mail in mails if not mail.has_label(GmailLabel.Processed)
        ]

        logging.info(
            f"MailCheck: skipped {len(mails) - len(unprocessed_mails)} mails already marked as Processed"
        )
        return unprocessed_mails

    def _fetch_mails_after_cutoff(
        self, cutoff_date: datetime
    ) -> list[FullMailResponse]:
        query = GmailQueryBuilder().after_date(cutoff_date).build()
        mails = self._gmail_client.fetch_mails(query)
        logging.info(
            f"MailCheck: fetched {len(mails)} mails after cutoff date {cutoff_date.isoformat()}"
        )
        return mails
