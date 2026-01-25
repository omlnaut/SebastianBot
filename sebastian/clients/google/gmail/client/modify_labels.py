from sebastian.protocols.gmail.models import GmailLabel


def _modify_labels(
    gmail_service,
    email_id: str,
    add_labels: list[GmailLabel] | None = None,
    remove_labels: list[GmailLabel] | None = None,
):
    add_label_ids = [tag.value for tag in (add_labels or [])]
    remove_label_ids = [tag.value for tag in (remove_labels or [])]
    modify_request = {
        "addLabelIds": add_label_ids,
        "removeLabelIds": remove_label_ids,
    }
    gmail_service.users().messages().modify(
        userId="me", id=email_id, body=modify_request
    ).execute()
