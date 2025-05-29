import json
import uuid

import boto3
import pytest
from fastapi.testclient import TestClient
from moto import mock_aws

from models.note_models import NoteCreated, NoteDB, NoteOut
from note_app.main import app


@pytest.fixture(autouse=True)
def _env(monkeypatch: pytest.MonkeyPatch):
    """
    Injects the tests' env variables.
    """
    monkeypatch.setenv("AWS_REGION", "us-west-2")
    monkeypatch.setenv("DYNAMODB_TABLE", "NotesTable")
    monkeypatch.setenv("S3_BUCKET_NAME", "MyNotesBucket")
    yield


def _client() -> TestClient:
    """
    Spin up moto mocks + create table/bucket, then returns a TestClient.
    """
    # arrange Mock dynamodb
    dynamodb = boto3.resource("dynamodb", region_name="us-west-2")
    dynamodb.create_table(
        TableName="NotesTable",
        KeySchema=[{"AttributeName": "note_id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "note_id", "AttributeType": "S"}],
        ProvisionedThroughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
    )
    # arrange mock s3
    s3 = boto3.client("s3", region_name="us-west-2")
    s3.create_bucket(
        Bucket="MyNotesBucket",
        CreateBucketConfiguration={"LocationConstraint": "us-west-2"},
    )

    return TestClient(app)


@mock_aws
def test_ping() -> None:
    """
    Testing health-check.
    """
    client = _client()
    response = client.get("api/v1/ping")

    assert response.status_code == 200
    assert response.json() == {"message": "pong"}


@mock_aws
def test_create_note_json_only():
    """
    Endpoint accepts *JSON-only* payloads and DOES NOT create an S3 object.
    """
    client = _client()
    payload = {"title": "JSON", "content": "only"}
    files = {"note_str": (None, json.dumps(payload), "application/json")}

    response = client.post("api/v1/notes", files=files)
    assert response.status_code == 201

    # validates that the note UUID is syntactically correct; ValueError if bad
    note_created = NoteCreated.model_validate(response.json())
    # no file was uploaded so the endpoint doesn't create an s3 key
    assert note_created.s3_key is None


@mock_aws
def test_create_note_with_file() -> None:
    """
    Endpoint stores the uploaded file in S3 and returns its object key
    """
    client = _client()

    payload = {"title": "File", "content": "with"}
    files = [
        ("note_str", (None, json.dumps(payload), "application/json")),
        ("file", ("dummy.txt", b"hi", "text/plain")),
    ]

    response = client.post("api/v1/notes", files=files)
    assert response.status_code == 201

    note_created = NoteCreated.model_validate(response.json())
    assert note_created.s3_key.startswith("notes/")

    # verify S3 object existence inside the moto mock
    s3 = boto3.client("s3")
    objs = s3.list_objects_v2(Bucket="MyNotesBucket", Prefix=note_created.s3_key)
    assert objs.get("KeyCount", 0) == 1, "Uploaded file not found in mocked S3!"


@mock_aws
def test_get_note_found() -> None:
    """
    Successfully fetch a previously created note.
    """
    client = _client()

    # insert a note into the mocked dDB table
    note_id = str(uuid.uuid4())
    note_db = NoteDB(
        note_id=note_id,
        title="Hello from Postman",
        content="Another dummyfile!",
        s3_key=f"notes/{note_id}/dummyfile.txt",
    )
    dynamodb = boto3.resource("dynamodb", region_name="us-west-2")
    table = dynamodb.Table("NotesTable")
    table.put_item(Item=note_db.model_dump())

    response = client.get(f"api/v1/notes/{note_id}")
    # assert status code
    assert response.status_code == 200

    # validate the NoteOut model
    note_out = NoteOut.model_validate(response.json())

    # dict types ... they should be equivalent here
    assert response.json() == note_db.model_dump()


@mock_aws
def test_get_note_not_found() -> None:
    """
    Requesting an unknown note_id yields 404 Not Found.
    """
    client = _client()
    # novel/unknown id that can't be in DB
    unknown_id = str(uuid.uuid4())

    response = client.get(f"api/v1/notes/{unknown_id}")

    # endpoint get_note raises a HTTPException(status_code=404, detail="Note not found")
    assert response.status_code == 404
    assert response.json()["detail"] == "Note not found"
