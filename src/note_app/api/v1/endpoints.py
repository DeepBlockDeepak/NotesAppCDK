import json
import os
import uuid
from functools import cache
from typing import Any, Optional

import boto3
from boto3.resources.base import ServiceResource
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from mypy_boto3_dynamodb.service_resource import Table

from models.note_models import NoteModel

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


@router.post("/notes")
def create_note(
    note_str: str = Form(...),
    file: UploadFile = File(None),
    aws: AWSClientFactory = Depends(get_aws_factory),
):
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
        aws.s3.upload_fileobj(file.file, aws.bucket_name, s3_key)

    item = {
        "note_id": note_id,
        "title": note.title,
        "content": note.content,
        "s3_key": s3_key,
    }
    aws.notes_table.put_item(Item=item)

    return {"note_id": note_id, "s3_key": s3_key}


@router.get("/notes/{note_id}")
def get_note(note_id: str, aws: AWSClientFactory = Depends(get_aws_factory)):
    resp = aws.notes_table.get_item(Key={"note_id": note_id})
    item = resp.get("Item")
    if not item:
        raise HTTPException(status_code=404, detail="Note not found")

    return item


@router.get("/ping")
def ping():
    """A simple testing endpoint."""
    return {"message": "pong"}
