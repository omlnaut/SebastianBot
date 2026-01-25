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
        return self.modify_labels(email_id, add_labels=[label])

    def modify_labels(
        self,
        email_id: str,
        add_labels: list[GmailLabel] | None = None,
        remove_labels: list[GmailLabel] | None = None,
    ) -> Result[str]:
        """
        Modify Gmail labels on a single email by adding and/or removing labels.

        Args:
            email_id: The Gmail message ID to modify
            add_labels: List of GmailLabels to add (optional)
            remove_labels: List of GmailLabels to remove (optional)

        Returns:
            Result[str] containing the email_id on success, or errors if the operation failed
        """
        try:
            # Skip if no operations requested
            if not add_labels and not remove_labels:
                logging.info(f"No label modifications requested for email {email_id}")
                return Result.from_item(item=email_id)

            # Build log message
            operations = []
            if add_labels:
                operations.append(
                    f"adding {', '.join(label.name for label in add_labels)}"
                )
            if remove_labels:
                operations.append(
                    f"removing {', '.join(label.name for label in remove_labels)}"
                )
            log_msg = f"Modifying labels for email {email_id}: {'; '.join(operations)}"
            logging.info(log_msg)

            self.gmail_client.modify_labels(
                email_id, add_labels=add_labels, remove_labels=remove_labels
            )

            logging.info(f"Successfully modified labels for email {email_id}")
            return Result.from_item(item=email_id)
        except Exception as e:
            error_msg = f"Failed to modify labels for email {email_id}: {str(e)}"
            logging.error(error_msg)
            return Result.from_item(errors=[error_msg])
