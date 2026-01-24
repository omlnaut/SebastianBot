from sebastian.protocols.gmail.models import GmailTag


def _modify_labels(
    gmail_service,
    email_id: str,
    add_labels: list[GmailTag] | None = None,
    remove_labels: list[GmailTag] | None = None,
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
