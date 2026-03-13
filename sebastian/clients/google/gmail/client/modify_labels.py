from sebastian.clients.google.gmail.client.service_wrapper import GmailServiceWrapper
from sebastian.domain.gmail import GmailLabel


def modify_labels(
    gmail_service: GmailServiceWrapper,
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
    gmail_service.modify_labels(email_id=email_id, body=modify_request)
