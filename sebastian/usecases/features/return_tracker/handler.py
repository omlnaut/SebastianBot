import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable, Sequence

from sebastian.domain.gmail import FullMailResponse
from sebastian.domain.side_effect import (
    CreateTask,
    ModifyMailLabel,
    SendMessage,
    SideEffect,
)
from sebastian.domain.task import TaskLists
from sebastian.usecases.shared.gemini_exceptions import (
    GeminiRetryConfiguration,
    TransientGeminiError,
)
from sebastian.usecases.shared.query_builder import GmailQueryBuilder
from sebastian.usecases.usecase_handler import UseCaseHandler

from .parsing import ReturnData, parse_return_email_html
from .protocols import GeminiClient, GmailClient

__all__ = ["Request", "Handler", "MailSubUseCase", "GmailClient", "GeminiClient"]


@dataclass
class Request:
    pass


class MailSubUseCase:
    def __init__(
        self,
        retry_configuration: GeminiRetryConfiguration,
        gemini_client_resolver: Callable[[], GeminiClient],
    ):
        self._retry_configuration = retry_configuration
        self._gemini_client_resolver = gemini_client_resolver

    def check_if_mail_matches(self, mail: FullMailResponse) -> bool:
        return _subject_matches(mail.subject) and _sender_matches(mail)

    def handle_mail(self, mail: FullMailResponse) -> Sequence[SideEffect]:
        handler = Handler(
            gemini_client=self._gemini_client_resolver(),
            retry_configuration=self._retry_configuration,
        )
        return handler.handle_mail(mail)


class Handler(UseCaseHandler[Request]):
    def __init__(
        self,
        gmail_client: GmailClient | None = None,
        gemini_client: GeminiClient | None = None,
        retry_configuration: GeminiRetryConfiguration | None = None,
    ):
        self._gmail_client = gmail_client
        self._gemini_client = gemini_client
        self._retry_configuration = retry_configuration or GeminiRetryConfiguration()

    def check_if_mail_matches(self, mail: FullMailResponse) -> bool:
        return _subject_matches(mail.subject) and _sender_matches(mail)

    def handle(self, request: Request) -> Sequence[SideEffect]:
        now = datetime.now(timezone.utc)
        mails = self._fetch_return_emails()

        effects: list[SideEffect] = []

        for mail in mails:
            effects.extend(self._handle_mail(mail, now))

        return effects

    def handle_mail(
        self,
        mail: FullMailResponse,
        now: datetime | None = None,
    ) -> Sequence[SideEffect]:
        if now is None:
            now = datetime.now(timezone.utc)

        return self._handle_mail(mail, now)

    def _handle_mail(
        self,
        mail: FullMailResponse,
        now: datetime,
    ) -> Sequence[SideEffect]:
        if self._gemini_client is None:
            raise ValueError("gemini_client is required")

        age = _mail_age(mail, now)
        if age is None:
            return _terminal_failure_effects(
                mail,
                reason=f"Invalid internalDate: {mail.internalDate}",
            )

        if age > self._retry_configuration.retry_horizon:
            return _terminal_failure_effects(
                mail,
                reason=f"Retry horizon exceeded ({age})",
            )

        try:
            return_data = _parse_with_transient_retry(
                mail.content,
                self._gemini_client,
                self._retry_configuration.immediate_retry_delay_seconds,
            )
            return [
                _map_to_create_task(return_data),
                ModifyMailLabel.MarkAsRead(mail.id),
                ModifyMailLabel.MarkAsProcessed(mail.id),
            ]
        except TransientGeminiError as e:
            logging.warning(
                f"Transient Gemini error for return notification {mail.id}. Keeping unread for retry. Error: {str(e)}"
            )
            return []
        except Exception as e:
            return _terminal_failure_effects(mail, reason=f"Parsing failed: {str(e)}")

    def _fetch_return_emails(self) -> Sequence[FullMailResponse]:
        if self._gmail_client is None:
            raise ValueError("gmail_client is required")

        mails = fetch_return_emails(self._gmail_client)
        return mails


def fetch_return_emails(
    gmail_client: GmailClient,
) -> Sequence[FullMailResponse]:
    """
    Fetch return emails from Amazon using the Gmail API, filtering by sender, subject, and date.
    Additionally filter the fetched emails to only include those that contain the inital return confirmation text.
    """
    query_parts = (
        GmailQueryBuilder()
        .from_email("rueckgabe@amazon.de")
        .subject("Ihre Rücksendung von", exact=False)
        .is_unread()
    )
    query = query_parts.build()
    mails = gmail_client.fetch_mails(query)
    logging.info(f"Fetched {len(mails)} return emails from Amazon")
    # this filter has to be done in-memory, because the Gmail API does not support searching for email content
    filtered_mails = [
        mail
        for mail in mails
        if "Deine Rückgabeanfrage wurde akzeptiert" in mail.content
    ]
    logging.info(f"Filtered {len(filtered_mails)} accepted return emails from Amazon")
    return filtered_mails


def _parse_with_transient_retry(
    html: str,
    gemini_client: GeminiClient,
    immediate_retry_delay_seconds: float,
) -> ReturnData:
    try:
        return parse_return_email_html(html, gemini_client)
    except TransientGeminiError:
        time.sleep(immediate_retry_delay_seconds)
        return parse_return_email_html(html, gemini_client)


def _mail_age(mail: FullMailResponse, now: datetime) -> timedelta | None:
    try:
        timestamp = int(mail.internalDate) / 1000
    except ValueError:
        return None

    received_at = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    return now - received_at


def _terminal_failure_effects(mail: FullMailResponse, reason: str) -> list[SideEffect]:
    return [
        SendMessage(
            message=(
                "Return Notification processing failed terminally. "
                f"mail_id={mail.id}; reason={reason}"
            )
        ),
        ModifyMailLabel.MarkAsRead(mail.id),
    ]


def _subject_matches(subject: str) -> bool:
    normalized_subject = subject.strip().casefold()
    return (
        normalized_subject.startswith("abgabebestätigung".casefold())
        or "rücksendung" in normalized_subject
        or "rückgabe" in normalized_subject
    )


def _sender_matches(mail: FullMailResponse) -> bool:
    return mail.from_email.strip().casefold() == "rueckgabe@amazon.de"


def _map_to_create_task(return_data: ReturnData) -> CreateTask:
    title = "Retoure"
    notes = (
        f"{return_data.item_title}\n"
        f"Abholort: {return_data.pickup_location}\n"
        f"Retoure bis: {return_data.return_date}\n"
        f"Order: {return_data.order_number}"
    )
    return CreateTask(title=title, notes=notes, tasklist=TaskLists.Default)
