from datetime import datetime, timedelta

from sebastian.clients.google.gmail.client import GmailClient
from sebastian.domain.gmail import GmailLabel
from sebastian.usecases.shared.query_builder import GmailQueryBuilder


def test_fetch_mails(gmail_client: GmailClient):
    date_24h_ago = datetime.now() - timedelta(hours=24)
    query = GmailQueryBuilder().after_date(date_24h_ago).build()

    emails = gmail_client.fetch_mails(query)

    assert isinstance(emails, list)
    assert len(emails) > 0
    assert all(isinstance(mail.subject, str) for mail in emails)


def test_fetch_mails_has_read_state(gmail_client: GmailClient):
    query = GmailQueryBuilder().on_date(datetime(2026, 1, 15)).build()

    emails = gmail_client.fetch_mails(query)

    assert len(emails) > 0
    assert all(isinstance(mail.is_read, bool) for mail in emails)

    target_mail = next((mail for mail in emails if mail.is_read), None)
    assert target_mail is not None, "Expected at least one already-read email"

    try:
        gmail_client.modify_labels(target_mail.id, add_labels=[GmailLabel.Unread])

        updated_mails = gmail_client.fetch_mails(query)
        updated_mail = next(
            (mail for mail in updated_mails if mail.id == target_mail.id), None
        )
        assert updated_mail is not None, "Email disappeared after updating labels"
        assert (
            updated_mail.is_read is False
        ), f"Expected email with subject {updated_mail.snippet[:20]} to be unread after adding UNREAD label"
    finally:
        gmail_client.modify_labels(target_mail.id, remove_labels=[GmailLabel.Unread])

    restored_mails = gmail_client.fetch_mails(query)
    restored_mail = next(
        (mail for mail in restored_mails if mail.id == target_mail.id), None
    )
    assert restored_mail is not None, "Email disappeared after restoring labels"
    assert (
        restored_mail.is_read is True
    ), f"Expected email with subject {restored_mail.snippet[:20]} to be read after removing UNREAD label"


def test_query_builder_on_date(gmail_client: GmailClient):
    query = (
        GmailQueryBuilder()
        .from_email("azure-noreply@microsoft.com")
        .after_date(datetime(2026, 1, 22))
        .build()
    )

    mails = gmail_client.fetch_mails(query)
    assert len(mails) >= 1, "No emails found on the specific date"


def test_query_builder_exclude_me(gmail_client: GmailClient):
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
