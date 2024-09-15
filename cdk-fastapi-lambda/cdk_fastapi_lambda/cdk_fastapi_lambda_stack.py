from aws_cdk import Stack, Duration, CfnOutput, RemovalPolicy
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import aws_iam as iam  # Import IAM
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
        user_config_table = os.getenv("USER_CONFIG_TABLE")

        # Check for missing environment variables and raise an error if any are missing
        if not all([discord_token, application_id, discord_public_key, user_config_table]):
            raise ValueError("One or more required environment variables are missing")

        # Define the Docker image asset, pointing to the root directory where the Dockerfile is located
        docker_image = DockerImageAsset(self, "DockerImage",
            directory="./"
        )
        
        # Define DynamoDB table (optional - only if you're creating a new table)
        self.user_config_table = dynamodb.Table(self, "StudyBotUserConfig",
            partition_key=dynamodb.Attribute(name="user", type=dynamodb.AttributeType.STRING),
            removal_policy=RemovalPolicy.DESTROY  # Remove table when the stack is destroyed (for testing)
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
                "USER_CONFIG_TABLE": user_config_table  
            }
        )

        # Grant Lambda function permissions to access DynamoDB table
        self.user_config_table.grant_read_write_data(fastapi_lambda)

        # Alternatively, add a custom IAM policy to the Lambda role
        fastapi_lambda.add_to_role_policy(
            iam.PolicyStatement(
                actions=["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:UpdateItem", "dynamodb:DeleteItem"],
                resources=[f"arn:aws:dynamodb:{self.region}:{self.account}:table/{user_config_table}"]
            )
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
