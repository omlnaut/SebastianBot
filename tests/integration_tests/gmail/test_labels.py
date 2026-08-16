from datetime import datetime
from time import sleep

from sebastian.clients.google.gmail.client import GmailClient
from sebastian.domain.gmail import FullMailResponse, GmailLabels
from sebastian.usecases.shared.query_builder import GmailQueryBuilder


def _fetch_mail(
    gmail_client: GmailClient, mail_id: str | None = None
) -> FullMailResponse:
    query = (
        GmailQueryBuilder()
        .from_email("azure-noreply@microsoft.com")
        .after_date(datetime(2026, 1, 22))
        .build()
    )
    mails = gmail_client.fetch_mails(query)
    assert len(mails) >= 1, "Expected at least one email"

    if mail_id is None:
        return mails[0]

    selected_mail = next((mail for mail in mails if mail.id == mail_id), None)
    assert selected_mail is not None, f"Could not find mail {mail_id} in fetched emails"
    return selected_mail


def test_modify_labels(gmail_client: GmailClient):
    """Test adding and removing labels from an email"""

    def assert_label_not_present(label_id: str, mail_id: str) -> None:
        mail = _fetch_mail(gmail_client, mail_id)
        assert (
            label_id not in mail.labelIds
        ), f"Label {test_label.name} still present after removal"

    def assert_label_present(label_id: str, mail_id: str) -> None:
        mail = _fetch_mail(gmail_client, mail_id)
        assert (
            label_id in mail.labelIds
        ), f"Label {test_label.name} not found after adding"

    test_label = GmailLabels.Processed
    target_mail = _fetch_mail(gmail_client)
    email_id = target_mail.id

    try:
        gmail_client.modify_labels(email_id, add_labels=[test_label])
        assert_label_present(test_label.label_id, email_id)

        include_query = (
            GmailQueryBuilder()
            .has_label(test_label)
            .from_email("azure-noreply@microsoft.com")
            .after_date(datetime(2026, 1, 22))
            .build()
        )
        exclude_query = (
            GmailQueryBuilder()
            .does_not_have_label(test_label)
            .from_email("azure-noreply@microsoft.com")
            .after_date(datetime(2026, 1, 22))
            .build()
        )

        included_mail_ids: set[str] = set()
        excluded_mail_ids: set[str] = set()
        for _ in range(5):
            included_mail_ids = {
                mail.id for mail in gmail_client.fetch_mails(include_query)
            }
            excluded_mail_ids = {
                mail.id for mail in gmail_client.fetch_mails(exclude_query)
            }
            if email_id in included_mail_ids and email_id not in excluded_mail_ids:
                break
            sleep(2)

        assert (
            email_id in included_mail_ids
        ), "Expected the labeled mail to appear in the include query"
        assert (
            email_id not in excluded_mail_ids
        ), "Expected the labeled mail to be excluded from the exclude query"

        gmail_client.modify_labels(email_id, remove_labels=[test_label])
        assert_label_not_present(test_label.label_id, email_id)
    finally:
        gmail_client.modify_labels(email_id, remove_labels=[test_label])


# todo: re-enable test
# def test_get_labels_contains_all_enum_labels(gmail_client: GmailClient):
#     labels = gmail_client.get_labels()
#     returned_label_ids = {label.id for label in labels}
#     expected_label_ids = {label.label_id for label in GmailLabels}

#     missing_label_ids = expected_label_ids - returned_label_ids
#     assert (
#         not missing_label_ids
#     ), f"Missing expected Gmail labels: {sorted(missing_label_ids)}"
