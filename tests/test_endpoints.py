import json
import uuid

import boto3
import pytest
from fastapi.testclient import TestClient
from moto import mock_aws

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
    assert response.status_code == 200

    body = response.json()

    # validate that the note UUID is syntactically correct; ValueError if bad
    uuid.UUID(body["note_id"])

    # no file was uploaded so the endpoint doesn't create an s3 key
    assert body["s3_key"] is None


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
    assert response.status_code == 200

    body = response.json()
    assert body["s3_key"].startswith("notes/")

    # verify S3 object existence inside the moto mock
    s3 = boto3.client("s3")
    objs = s3.list_objects_v2(Bucket="MyNotesBucket", Prefix=body["s3_key"])
    assert objs.get("KeyCount", 0) == 1, "Uploaded file not found in mocked S3!"
