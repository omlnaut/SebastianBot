from cloud.dependencies.clients import resolve_gmail_client
from sebastian.usecases.features import return_tracker
import pytest

from sebastian.usecases.features.return_tracker.handler import fetch_return_emails
from datetime import datetime


@pytest.fixture
def client() -> return_tracker.GmailClient:
    return resolve_gmail_client()


def test_fetch_mails(client: return_tracker.GmailClient):
    mails = fetch_return_emails(
        gmail_client=client,
        after_date=datetime(2026, 4, 5),
        before_date=datetime(2026, 4, 9),
    )
    tap_mails = [mail for mail in mails if "Tapo TP-Link" in mail.content]

    assert len(tap_mails) == 1
