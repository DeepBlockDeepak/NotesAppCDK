import os
from functools import cache
from typing import Any, Optional

import boto3
from boto3.resources.base import ServiceResource
from mypy_boto3_dynamodb.service_resource import Table

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
