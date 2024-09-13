import aws_cdk as core
import aws_cdk.assertions as assertions

from cdk_fastapi_lambda.cdk_fastapi_lambda_stack import CdkFastapiLambdaStack

# example tests. To run these tests, uncomment this file along with the example
# resource in cdk_fastapi_lambda/cdk_fastapi_lambda_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = CdkFastapiLambdaStack(app, "cdk-fastapi-lambda")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
