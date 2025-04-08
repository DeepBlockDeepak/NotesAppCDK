from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
import boto3
import os
import uuid

from app.models.note_models import NoteModel

app = FastAPI()
dynamodb = boto3.resource("dynamodb") # stores the Note metadata (note ID, title, references to S3 object, maybe timestamps)
table = dynamodb.Table(os.environ.get("DYNAMODB_TABLE", "NotesTable"))
s3_client = boto3.client("s3") # stores the files
bucket_name = os.environ.get("S3_BUCKET_NAME", "MyNotesBucket")


@app.post("/notes")
def create_note(note: NoteModel, file: UploadFile = File(None)):
    """
     Creates a Note in DynamoDB (and a file attachment stored in S3).

    Args:
        note (NoteModel)
        file (UploadFile, optional)

    Returns:
        dict: Successful message (consider a validation model)
    """
    note_id = str(uuid.uuid4())
    s3_key = None

    if file:
        s3_key = f"notes/{note_id}/{file.filename}"
        s3_client.upload_fileobj(file.file, bucket_name, s3_key)

    item = {
        "note_id": note_id,
        "title" : note.title,
        "content": note.content,
        "s3_key": s3_key
    }
    table.put(Item=item)
    
    return {"note_id": note_id, "s3_key": s3_key}




@app.get("/ping")
def ping():
    return {"message": "pong"}
