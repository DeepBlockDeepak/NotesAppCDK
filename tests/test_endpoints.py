# tests/test_notes_endpoints.py
import json
import uuid
import boto3
import pytest
from fastapi.testclient import TestClient
from moto import mock_aws


from app.main import app

@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("AWS_REGION", "us-west-2")
    monkeypatch.setenv("DYNAMODB_TABLE", "NotesTable")
    monkeypatch.setenv("S3_BUCKET_NAME", "MyNotesBucket")
    yield


def _client():
    """
    Spin up moto mocks + create table/bucket, then return a TestClient.
    """
    dynamodb = boto3.resource("dynamodb", region_name="us-west-2")
    dynamodb.create_table(
        TableName="NotesTable",
        KeySchema=[{"AttributeName": "note_id", "KeyType": "HASH"}],
        AttributeDefinitions=[{"AttributeName": "note_id", "AttributeType": "S"}],
        ProvisionedThroughput={"ReadCapacityUnits": 5, "WriteCapacityUnits": 5},
    )
    s3 = boto3.client("s3", region_name="us-west-2")
    s3.create_bucket(Bucket="MyNotesBucket", CreateBucketConfiguration={"LocationConstraint": "us-west-2"},)
    
    return TestClient(app)


@mock_aws
def test_ping():
    """
    Tests the toy ping/pong endpoint
    """
    c = _client()
    r = c.get("api/v1/ping")

    assert r.status_code == 200
    assert r.json() == {"message": "pong"}


@mock_aws
def test_create_note_json_only():
    c = _client()
    payload = {"title": "JSON", "content": "only"}
    files = {"note_str": (None, json.dumps(payload), "application/json")}

    r = c.post("api/v1/notes", files=files)
    assert r.status_code == 200

    body = r.json()
    uuid.UUID(body["note_id"])
    assert body["s3_key"] is None


@mock_aws
def test_create_note_with_file():
    c = _client()
    payload = {"title": "File", "content": "with"}
    files = [
        ("note_str", (None, json.dumps(payload), "application/json")),
        ("file", ("dummy.txt", b"hi", "text/plain")),
    ]

    r = c.post("api/v1/notes", files=files)
    assert r.status_code == 200

    body = r.json()
    assert body["s3_key"].startswith("notes/")
