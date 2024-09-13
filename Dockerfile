# Use the AWS Lambda Python 3.11 base image
FROM public.ecr.aws/lambda/python:3.11

# Copy requirements.txt to the Lambda task root
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Install dependencies
RUN pip install -r requirements.txt

# Copy the app folder to the Lambda task root
COPY app/ ${LAMBDA_TASK_ROOT}/

# Set the CMD to point to the Lambda handler
CMD ["main.handler"]
