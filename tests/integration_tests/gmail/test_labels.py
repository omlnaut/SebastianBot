from datetime import datetime

from sebastian.protocols.gmail import GmailLabel
from sebastian.protocols.gmail.IClient import IGmailClient
from sebastian.protocols.gmail.models import FullMailResponse
from sebastian.shared.gmail.query_builder import GmailQueryBuilder


def test_modify_labels(gmail_client: IGmailClient):
    """Test adding and removing labels from an email"""

    def fetch_mail() -> FullMailResponse:
        query = (
            GmailQueryBuilder()
            .from_email("azure-noreply@microsoft.com")
            .after_date(datetime(2026, 1, 22))
            .build()
        )
        mails = gmail_client.fetch_mails(query)
        assert len(mails) == 1, "Expected exactly one email"
        return mails[0]

    def assert_label_not_present(label_id: str) -> FullMailResponse:
        mail = fetch_mail()
        assert (
            label_id not in mail.labelIds
        ), f"Label {test_label.name} still present after removal"
        return mail

    def assert_label_present(label_id: str) -> FullMailResponse:
        mail = fetch_mail()
        assert (
            label_id in mail.labelIds
        ), f"Label {test_label.name} not found after adding"
        return mail

    test_label = GmailLabel.ToRead
    tag_label_id = test_label.value
    email_id = assert_label_not_present(tag_label_id).id

    try:
        # Add the label and verify
        gmail_client.modify_labels(email_id, add_labels=[test_label])
        assert_label_present(tag_label_id)

        # Remove the label and verify
        gmail_client.modify_labels(email_id, remove_labels=[test_label])
        assert_label_not_present(tag_label_id)
    finally:
        # Cleanup: ensure label is removed even if test fails
        gmail_client.modify_labels(email_id, remove_labels=[test_label])
