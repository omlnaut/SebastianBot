import uuid
from datetime import datetime

import azure.functions as func
from pydantic import BaseModel, Field

from sebastian.protocols.gmail import GmailLabel


class ArchiveEmailEventGrid(BaseModel):
    title: str = Field(
        ...,
        description="Title of the email to archive.",
    )


class PutEmailInToReadEventGrid(BaseModel):
    title: str = Field(
        ...,
        description="Title of the email to mark as to-read.",
    )


class ModifyMailLabelEventGrid(BaseModel):
    email_id: str = Field(
        ...,
        description="Gmail message ID to modify",
    )
    add_labels: list[GmailLabel] | None = Field(
        default=None,
        description="List of GmailLabels to add (e.g., ['ToRead'])",
    )
    remove_labels: list[GmailLabel] | None = Field(
        default=None,
        description="List of GmailLabels to remove",
    )

    def to_output(self) -> func.EventGridOutputEvent:
        return func.EventGridOutputEvent(
            id=str(uuid.uuid4()),
            data=self.model_dump(mode="json"),
            subject="modify_mail_label",
            event_type="modify_mail_label_event",
            event_time=datetime.now(),
            data_version="1.0",
        )
