import aws_cdk as cdk
from constructs import Construct
from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_dynamodb as dynamodb,
    aws_s3 as s3,
    aws_iam as iam,
    Duration
)

class MyStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)
        # Example: define resources here (Lambda, S3, DynamoDB, etc.)
        # S3 bucket
        # my_bucket = s3.Bucket(self, "MyNotesBucket")

        # DynamoDB table
        # notes_table = dynamodb.Table(
        #     self,
        #     "NotesTable",
        #     partition_key=dynamodb.Attribute(
        #         name="note_id",
        #         type=dynamodb.AttributeType.STRING
        #     )
        # )

        # Lambda function
        # lambda_fn = _lambda.Function(
        #     self,
        #     "FastApiLambda",
        #     runtime=_lambda.Runtime.PYTHON_3_9,
        #     handler="main.app",         # if using Mangum do "main.lambda_handler"
        #     code=_lambda.Code.from_asset("app/"),  # or from Docker build
        #     environment={
        #         "DYNAMODB_TABLE": notes_table.table_name,
        #         "S3_BUCKET_NAME": my_bucket.bucket_name
        #     },
        #     timeout=Duration.seconds(30),
        # )

        # Grant Lambda access to S3 and DynamoDB
        # my_bucket.grant_read_write(lambda_fn)
        # notes_table.grant_read_write_data(lambda_fn)

        # API Gateway (REST API) integrated with Lambda
        # api = apigw.LambdaRestApi(
        #     self,
        #     "MyFastApiGateway",
        #     handler=lambda_fn,
        # )

        # Optionally output the API endpoint
        # self.api_url = api.url

