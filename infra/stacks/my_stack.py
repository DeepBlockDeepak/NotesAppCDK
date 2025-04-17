import aws_cdk as cdk
from aws_cdk import Duration, Stack
from aws_cdk import aws_apigateway as apigw
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_s3 as s3
from constructs import Construct


class MyStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # S3 bucket - storing files
        my_bucket = s3.Bucket(self, "MyNotesBucket")

        # DynamoDB table for Notes data
        notes_table = dynamodb.Table(
            self,
            "NotesTable",
            partition_key=dynamodb.Attribute(
                name="note_id", type=dynamodb.AttributeType.STRING
            ),
        )

        # Lambda
        lambda_fn = _lambda.DockerImageFunction(
            self,
            "FastApiLambda",
            code=_lambda.DockerImageCode.from_image_asset(
                directory=".",
                file="Dockerfile",
                platform=cdk.aws_ecr_assets.Platform.LINUX_AMD64,
            ),
            environment={
                "DYNAMODB_TABLE": notes_table.table_name,
                "S3_BUCKET_NAME": my_bucket.bucket_name,
            },
            timeout=Duration.seconds(30),
        )

        # grant Lambda access to S3 and DynamoDB
        my_bucket.grant_read_write(lambda_fn)
        notes_table.grant_read_write_data(lambda_fn)

        # API Gateway -> route HTTP reqs to FastApiLambda
        api = apigw.LambdaRestApi(
            self,
            "MyFastApiGateway",
            handler=lambda_fn,
        )

        # API key
        api_key = apigw.ApiKey(
            self, "MyApiKey", api_key_name="MyKey", description="Used for my test stack"
        )

        # usage plan
        usage_plan = apigw.UsagePlan(
            self,
            "UsagePlan",
            name="BasicUsagePlan",
            throttle=apigw.ThrottleSettings(rate_limit=10, burst_limit=2),
        )

        # attach plan to API + stage
        usage_plan.add_api_stage(stage=api.deployment_stage, api=api)

        # create a subresource for /notes
        notes_resource = api.root.add_resource("notes")

        # add a POST method to /notes that requires an API key
        notes_resource.add_method(
            "POST", apigw.LambdaIntegration(lambda_fn), api_key_required=True
        )

        # associate API key with usage plan
        usage_plan.add_api_key(api_key)

        # output the API endpoint
        self.api_url = api.url
