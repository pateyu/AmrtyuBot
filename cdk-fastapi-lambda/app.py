#!/usr/bin/env python3
import os
import aws_cdk as cdk
from cdk_fastapi_lambda.cdk_fastapi_lambda_stack import CdkFastapiLambdaStack

app = cdk.App()
CdkFastapiLambdaStack(app, "CdkFastapiLambdaStack", 
    env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION'))
)

app.synth()
