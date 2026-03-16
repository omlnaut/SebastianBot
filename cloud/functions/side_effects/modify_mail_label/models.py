from typing import Self, override

from pydantic import BaseModel, Field

from cloud.helper.event_grid import EventGridModel
from sebastian.domain.gmail import GmailLabel
from sebastian.protocols.models import ModifyMailLabel


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


class ModifyMailLabelEventGrid(EventGridModel[ModifyMailLabel]):
    email_id: str = Field(
        ...,
        description="Gmail message ID to modify",
    )
    add_labels: list[GmailLabel] = Field(
        default_factory=list[GmailLabel],
        description="List of GmailLabels to add (e.g., ['ToRead'])",
    )
    remove_labels: list[GmailLabel] = Field(
        default_factory=list[GmailLabel],
        description="List of GmailLabels to remove",
    )

    @classmethod
    @override
    def from_application(cls, app_event: ModifyMailLabel) -> Self:
        return cls(
            email_id=app_event.email_id,
            add_labels=app_event.add_labels,
            remove_labels=app_event.remove_labels,
        )
