import uuid
from datetime import datetime

import azure.functions as func
from pydantic import BaseModel, Field

from cloud.helper.event_grid import EventGridMixin
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


class ModifyMailLabelEventGrid(EventGridMixin, BaseModel):
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
