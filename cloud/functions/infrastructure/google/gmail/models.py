from pydantic import BaseModel, Field


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
