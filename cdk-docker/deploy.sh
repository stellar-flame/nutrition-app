#!/bin/bash

# This script automates the Docker build, push to ECR, and CDK deployment.
# It ensures a Lambda-compatible image by manually controlling the build process.

set -e # Exit immediately if a command exits with a non-zero status.

# --- Configuration ---
# The AWS Region where your ECR repository and CDK stack are located.
AWS_REGION="us-east-1"
# The name of the ECR repository defined in your cdk-docker/app.ts file.
ECR_REPO_NAME="nutrition-app-repo"
# The tag for your Docker image. 'latest' is used by default in the CDK app.
IMAGE_TAG="latest"
# --- End Configuration ---

echo "Starting deployment process..."

# 1. Get AWS Account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
if [ -z "$AWS_ACCOUNT_ID" ]; then
    echo "Error: Could not retrieve AWS Account ID. Please ensure you are logged in to the AWS CLI."
    exit 1
fi
echo "AWS Account ID: $AWS_ACCOUNT_ID"

# 2. Construct the full ECR repository URI
ECR_REPO_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO_NAME}"
echo "ECR Repository URI: $ECR_REPO_URI"

# 3. Deploy CDK stack first to create ECR repository (will fail on Lambda but that's OK)
echo "Deploying CDK stack to create ECR repository..."
set +e  # Temporarily allow failures
npx cdk deploy --require-approval never 2>/dev/null || echo "Expected failure - Lambda image doesn't exist yet"
set -e  # Re-enable exit on error

# 4. Log in to Amazon ECR
echo "Logging in to Amazon ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REPO_URI
echo "ECR login successful."

# 5. Build the Docker image for Lambda compatibility
echo "Building Docker image for Lambda..."
# We use BuildKit with explicit provenance=false to avoid manifest issues with AWS Lambda.
# The build context is the ../backend directory relative to this script.
docker build --provenance=false -t "${ECR_REPO_URI}:${IMAGE_TAG}" -f ../backend/Dockerfile ../backend
echo "Docker image built successfully."

# 6. Push the image to ECR
echo "Pushing image to ECR..."
docker push "${ECR_REPO_URI}:${IMAGE_TAG}"
echo "Image pushed successfully to ECR."

# 7. Deploy the CDK stack again - now with the image available
echo "Deploying CDK stack with image..."
npx cdk deploy --require-approval never
echo "CDK deployment completed successfully!"

# --- Final Outputs ---
# The CDK stack will output the API Gateway URL and other important values.
echo "Deployment finished. Check the CDK output for your API URL."
