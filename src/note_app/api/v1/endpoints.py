import os
import uuid
from functools import cache
from typing import Any, Optional

import boto3
from boto3.resources.base import ServiceResource
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from mypy_boto3_dynamodb.service_resource import Table

from models.note_models import NoteCreated, NoteDB, NoteIn, NoteOut

router = APIRouter()


class AWSClientFactory:
    def __init__(self, region: Optional[str] = None):
        self.region = region or os.environ.get("AWS_REGION") or "us-west-2"

    @property
    @cache
    def s3(self) -> Any:
        return boto3.client("s3", region_name=self.region)

    @property
    def bucket_name(self) -> str:
        return os.environ["S3_BUCKET_NAME"]

    @property
    @cache
    def dynamodb_resource(self) -> ServiceResource:
        return boto3.resource("dynamodb", region_name=self.region)

    @property
    def notes_table(self) -> Table:
        table_name = os.environ["DYNAMODB_TABLE"]
        return self.dynamodb_resource.Table(table_name)


@cache
def get_aws_factory() -> AWSClientFactory:
    return AWSClientFactory()


@router.post("/notes", response_model=NoteCreated, status_code=201)
def create_note(
    note_str: str = Form(...),
    file: UploadFile = File(None),
    aws_client: AWSClientFactory = Depends(get_aws_factory),
) -> NoteCreated:
    """
    Creates a Note in DynamoDB (and a file attachment stored in S3).

    Args:
        note_str: Payload supplied with 'title' of the File and 'content' description of the File.
        Ex:
            {"title":"example_note.txt","content":"Contains some foobar."}

        file: Your local file.
        aws_client: The boto3 client.

    Returns:
        NoteCreated: Succesfully created Note
    """
    # validate the input note-json:str body
    # TODO wrap in try/except ValidationError and throw HTTPException(422) for custom error
    note_in = NoteIn.model_validate_json(note_str)

    note_id = str(uuid.uuid4())
    s3_key: Optional[str] = None

    if file:
        s3_key = f"notes/{note_id}/{file.filename}"
        aws_client.s3.upload_fileobj(file.file, aws_client.bucket_name, s3_key)

    # validate the dynamo DB datum
    db_item = NoteDB(
        note_id=note_id, title=note_in.title, content=note_in.content, s3_key=s3_key
    )
    aws_client.notes_table.put_item(Item=db_item.model_dump())

    return NoteCreated(note_id=note_id, s3_key=s3_key)


@router.get("/notes/{note_id}", response_model=NoteOut)
def get_note(
    note_id: uuid.UUID, aws_client: AWSClientFactory = Depends(get_aws_factory)
) -> NoteOut:
    """
    Finds a requested note via the Notes Table. If found, the s3 key is supplied.

    Args:
        note_id (uuid.UUID): _description_
        aws_client (AWSClientFactory, optional): _description_. Defaults to Depends(get_aws_factory).

    Raises:
        HTTPException: _description_

    Returns:
        NoteOut: _description_
    """
    resp = aws_client.notes_table.get_item(Key={"note_id": str(note_id)})
    item = resp.get("Item")

    # validate item as a NoteOut
    if not item:
        raise HTTPException(status_code=404, detail="Note not found")

    # validate the returned NoteDB from dynamoDB internally
    note_db = NoteDB.model_validate(item)
    return NoteOut(**note_db.model_dump())


@router.get("/ping")
def ping():
    """A simple testing endpoint."""
    return {"message": "pong"}
