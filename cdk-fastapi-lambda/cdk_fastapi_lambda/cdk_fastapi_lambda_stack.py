from aws_cdk import Stack, Duration, CfnOutput, aws_dynamodb as dynamodb
from constructs import Construct
from aws_cdk.aws_lambda import DockerImageFunction, DockerImageCode, FunctionUrlAuthType, HttpMethod, Architecture
from aws_cdk.aws_ecr_assets import DockerImageAsset
import os

class StudyBotLambdaStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Load environment variables
        discord_token = os.getenv("DISCORD_TOKEN")
        application_id = os.getenv("APPLICATION_ID")
        discord_public_key = os.getenv("DISCORD_PUBLIC_KEY")
        canvas_api_key = os.getenv("CANVAS_API_KEY")
        canvas_api_url = os.getenv("CANVAS_API_URL")

        # Check for missing environment variables and raise an error if any are missing
        if not all([discord_token, application_id, discord_public_key, canvas_api_key, canvas_api_url]):
            raise ValueError("One or more required environment variables are missing")

        # Define the Docker image asset, pointing to the root directory where the Dockerfile is located
        docker_image = DockerImageAsset(self, "DockerImage",
            directory="./"
        )
        self.user_config_table = dynamodb.Table(self, "StudyBotUserConfig",
            partition_key=dynamodb.Attribute(name="UserId", type=dynamodb.AttributeType.STRING),
            removal_policy=cdk.RemovalPolicy.DESTROY  # Remove table when the stack is destroyed (for testing)
        )


        # Create a Lambda function using the Docker image
        fastapi_lambda = DockerImageFunction(self, "StudyBotLambda",
            code=DockerImageCode.from_image_asset(directory="./"),  
            memory_size=1024,
            timeout=Duration.seconds(10),
            architecture=Architecture.ARM_64,  
            environment={
                "DISCORD_TOKEN": discord_token,
                "APPLICATION_ID": application_id,
                "DISCORD_PUBLIC_KEY": discord_public_key,
                "CANVAS_API_KEY": canvas_api_key,
                "CANVAS_API_URL": canvas_api_url
            }
        )

        # Add a Function URL for the Lambda function with proper CORS configuration
        function_url = fastapi_lambda.add_function_url(
            auth_type=FunctionUrlAuthType.NONE,
            cors={
                "allowed_origins": ["*"],
                "allowed_methods": [HttpMethod.ALL],  # Correctly defining allowed methods
                "allowed_headers": ["*"],
            }
        )

        # Output the Function URL and Lambda ARN
        CfnOutput(self, "FunctionUrl", value=function_url.url, description="The Lambda Function URL")
        CfnOutput(self, "LambdaARN", value=fastapi_lambda.function_arn, description="The Lambda Function ARN")


