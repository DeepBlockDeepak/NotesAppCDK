import json
import os
import uuid
from functools import lru_cache
from typing import Any, Optional

import boto3
from boto3.resources.base import ServiceResource
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from mypy_boto3_dynamodb.service_resource import Table

from src.note_app.models.note_models import NoteModel

router = APIRouter()
dynamodb = boto3.resource(
    "dynamodb"
)  # stores the Note metadata (note ID, title, references to S3 object, maybe timestamps)
table = dynamodb.Table(os.environ.get("DYNAMODB_TABLE", "NotesTable"))
s3_client = boto3.client("s3")  # stores the files
bucket_name = os.environ.get("S3_BUCKET_NAME", "MyNotesBucket")


# @NOTE: future class for dependency injecting the clients
class AWSClientFactory:
    def __init__(self, region: Optional[str] = None):
        self.region = region or os.environ.get("AWS_REGION") or "us-west-2"

    @property
    @lru_cache()
    def s3(self) -> Any:
        return boto3.client("s3", region_name=self.region)

    @property
    @lru_cache()
    def dynamodb_resource(self) -> ServiceResource:
        return boto3.resource("dynamodb", region_name=self.region)

    @property
    def notes_table(self) -> Table:
        table_name = os.environ["DYNAMODB_TABLE"]
        return self.dynamodb_resource.Table(table_name)


@lru_cache()
def get_aws_factory() -> AWSClientFactory:
    return AWSClientFactory()


@router.post("/notes")
def create_note(note_str: str = Form(...), file: UploadFile = File(None)):
    """
    Creates a Note in DynamoDB (and a file attachment stored in S3).

    Returns:
        dict: Successful message (consider a validation model)
    """
    # validate the input note-json body
    note_dict = json.loads(note_str)
    note = NoteModel(**note_dict)

    note_id = str(uuid.uuid4())
    s3_key = None

    if file:
        s3_key = f"notes/{note_id}/{file.filename}"
        s3_client.upload_fileobj(file.file, bucket_name, s3_key)

    item = {
        "note_id": note_id,
        "title": note.title,
        "content": note.content,
        "s3_key": s3_key,
    }
    table.put_item(Item=item)

    return {"note_id": note_id, "s3_key": s3_key}


@router.get("/notes/{note_id}")
def get_note(note_id: str):
    resp = table.get_item(Key={"note_id": note_id})
    item = resp.get("Item")
    if not item:
        raise HTTPException(status_code=404, detail="Note not found")

    return item


@router.get("/ping")
def ping():
    """A simple testing endpoint."""
    return {"message": "pong"}
