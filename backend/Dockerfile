# syntax=docker/dockerfile:1.4
FROM --platform=linux/amd64 public.ecr.aws/lambda/python:3.11

# Set working directory
WORKDIR ${LAMBDA_TASK_ROOT}

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set the CMD to your handler
CMD ["main.handler"]

# Ensure OCI compatibility for Lambda
LABEL org.opencontainers.image.title="nutrition-app-lambda"
LABEL org.opencontainers.image.description="FastAPI nutrition app for AWS Lambda"
