from typing import Optional

from pydantic import UUID4, BaseModel, Field


# original note-base idea
class NoteModel(BaseModel):
    title: str
    content: str


class NoteBase(BaseModel):
    """
    Client-supplied meta-data which is later persisted in DynamoDB
    """

    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)


class NoteIn(NoteBase):
    """
    Same as NoteBase for now.
    Kept separate/decoupled for future evolution, like :
        * allowing the client to POST extra fields later in the /notes.
                while keeping the DB shape stable with NoteDB.
    """

    pass


class NoteCreated(BaseModel):
    """
    Return from POST /notes.
    """

    note_id: UUID4
    s3_key: Optional[str] = None


class NoteOut(NoteBase):
    """
    Return from GET /notes/{id}.
    """

    note_id: UUID4
    s3_key: Optional[str] = None


class NoteDB(NoteOut):
    """
    Data shape to write to/read from DynamoDB.
    """

    note_id: str  # UUID serialised to str
