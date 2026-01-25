from datetime import datetime, timedelta

from sebastian.protocols.gmail.IClient import IGmailClient
from sebastian.shared.gmail.query_builder import GmailQueryBuilder


def test_fetch_mails(gmail_client: IGmailClient):
    date_24h_ago = datetime.now() - timedelta(hours=24)
    query = GmailQueryBuilder().after_date(date_24h_ago).build()

    emails = gmail_client.fetch_mails(query)

    assert isinstance(emails, list)
    assert len(emails) > 0


def test_query_builder_on_date(gmail_client: IGmailClient):
    query = (
        GmailQueryBuilder()
        .from_email("azure-noreply@microsoft.com")
        .after_date(datetime(2026, 1, 22))
        .build()
    )

    mails = gmail_client.fetch_mails(query)
    assert len(mails) == 1, "No emails found on the specific date"


def test_query_builder_exclude_me(gmail_client: IGmailClient):
    base_query = (
        GmailQueryBuilder()
        .subject("Take a look!", exact=False)
        .from_email("oneironaut.oml@gmail.com")
        .after_date(datetime(2025, 12, 18))
    )

    mails_with_me = gmail_client.fetch_mails(base_query.build())
    assert len(mails_with_me) > 0

    mails_without_me = gmail_client.fetch_mails(base_query.exclude_me().build())
    assert len(mails_without_me) == 0
