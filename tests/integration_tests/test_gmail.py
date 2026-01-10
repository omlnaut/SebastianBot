import pytest
from datetime import datetime, timedelta
from cloud.dependencies.clients import resolve_gmail_client
from sebastian.protocols.gmail.IClient import IGmailClient
from sebastian.shared.gmail.query_builder import GmailQueryBuilder


@pytest.fixture
def gmail_client() -> IGmailClient:
    return resolve_gmail_client()


def test_fetch_mails(gmail_client: IGmailClient):
    date_24h_ago = datetime.now() - timedelta(hours=24)
    query = GmailQueryBuilder().after_date(date_24h_ago).build()

    emails = gmail_client.fetch_mails(query)

    assert isinstance(emails, list)
    assert len(emails) > 0
