from pydantic import BaseModel, Field


class ArchiveEmailEvent(BaseModel):
    title: str = Field(
        ...,
        description="Title of the email to archive.",
    )


class PutEmailInToReadEvent(BaseModel):
    title: str = Field(
        ...,
        description="Title of the email to mark as to-read.",
    )
