import logging

from sebastian.protocols.gmail import IGmailClient, GmailLabel
from sebastian.shared import Result


class Handler:
    def __init__(self, gmail_client: IGmailClient):
        self.gmail_client = gmail_client

    def add_label(self, email_id: str, label: GmailLabel) -> Result[str]:
        """
        Add a Gmail label to a single email.

        Args:
            email_id: The Gmail message ID to label
            label: The GmailLabel to apply

        Returns:
            Result[str] containing the email_id on success, or errors if the operation failed
        """
        try:
            logging.info(f"Adding label {label.name} to email {email_id}")

            self.gmail_client.modify_labels(email_id, add_labels=[label])

            logging.info(f"Successfully added label {label.name} to email {email_id}")
            return Result.from_item(item=email_id)
        except Exception as e:
            error_msg = (
                f"Failed to add label {label.name} to email {email_id}: {str(e)}"
            )

            logging.error(error_msg)
            return Result.from_item(errors=[error_msg])
