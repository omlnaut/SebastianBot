from asyncio.log import logger
import logging

from sebastian.protocols.gmail import IGmailClient, GmailLabel
from sebastian.shared import Result


class AddTagToMail:
    def __init__(self, gmail_client: IGmailClient):
        self.gmail_client = gmail_client

    def add_tag(self, email_id: str, tag: GmailLabel) -> Result[str]:
        """
        Add a Gmail tag/label to a single email.

        Args:
            email_id: The Gmail message ID to tag
            tag: The GmailTag to apply

        Returns:
            Result[str] containing the email_id on success, or errors if the operation failed
        """
        try:
            logging.info(f"Adding tag {tag.name} to email {email_id}")

            self.gmail_client.modify_labels(email_id, add_labels=[tag])

            logging.info(f"Successfully added tag {tag.name} to email {email_id}")
            return Result.from_item(item=email_id)
        except Exception as e:
            error_msg = f"Failed to add tag {tag.name} to email {email_id}: {str(e)}"

            logging.error(error_msg)
            return Result.from_item(errors=[error_msg])
