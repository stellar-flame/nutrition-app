# Nutrition App API - AWS Lambda Deployment Guide

This guide provides instructions for deploying the Nutrition App API to AWS Lambda using Docker containers.

## Prerequisites

- AWS CLI installed and configured with appropriate permissions
- Docker installed and running
- An AWS account with access to Lambda, ECR, RDS, and API Gateway services

## Deployment Options

### Option 1: Manual Deployment

1. **Build and push the Docker image to ECR**:

   ```bash
   # Login to ECR
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <your-aws-account-id>.dkr.ecr.us-east-1.amazonaws.com
   
   # Create ECR repository (if it doesn't exist)
   aws ecr create-repository --repository-name nutrition-app-api --region us-east-1
   
   # Build the Docker image
   docker buildx build --platform linux/amd64 --load --provenance=false -t nutrition-app-api:latest .

   #docker build -t nutrition-app-api .
   
   # Tag the image
   docker tag nutrition-app-api:latest <your-aws-account-id>.dkr.ecr.us-east-1.amazonaws.com/nutrition-app-api:latest
   
   # Push the image to ECR
   docker push <your-aws-account-id>.dkr.ecr.us-east-1.amazonaws.com/nutrition-app-api:latest
   ```

2. **Create a Lambda function**:

   - Go to the AWS Lambda console
   - Create a new function with "Container image" option
   - Select the image you pushed to ECR
   - Configure environment variables (see .env.lambda for required variables)
   - Configure VPC settings if connecting to RDS in a VPC
   - Set memory to at least 512MB and timeout to 30 seconds

   # OR
   aws lambda create-function --function-name nutrition-api --package-type Image --code ImageUri=<your-aws-account-id>.dkr.ecr.us-east-1.amazonaws.com/nutrition-api:latest --role arn:aws:iam::<your-aws-account-id>:role/nutrition-app-lambda-role --timeout 30 --memory-size 512 --region us-east-1


3. **Create an API Gateway**:

   - Create a new REST API
   - Create a resource with path `/{proxy+}` and ANY method
   - Set up the integration with your Lambda function
   - Deploy the API to a stage (e.g., "prod")

### Option 2: Automated Deployment with CloudFormation

1. **Deploy the CloudFormation template**:

   ```bash
   aws cloudformation create-stack \
     --stack-name nutrition-app-infrastructure \
     --template-body file://cloudformation-template.yaml \
     --parameters \
       ParameterKey=DBPassword,ParameterValue=<your-db-password> \
       ParameterKey=OpenAIApiKey,ParameterValue=<your-openai-api-key> \
       ParameterKey=FirebaseProjectId,ParameterValue=<your-firebase-project-id> \
       ParameterKey=FirebasePrivateKey,ParameterValue=<your-firebase-private-key> \
       ParameterKey=FirebaseClientEmail,ParameterValue=<your-firebase-client-email> \
     --capabilities CAPABILITY_IAM
   ```

2. **Build and deploy the Docker image**:

   ```bash
   # Run the deployment script
   ./deploy_lambda.sh
   ```

### Option 3: Using the Deployment Script

The included `deploy_lambda.sh` script automates the process of building and deploying the Docker image to AWS Lambda:

1. **Make the script executable**:

   ```bash
   chmod +x deploy_lambda.sh
   ```

2. **Run the script**:

   ```bash
   ./deploy_lambda.sh
   ```

## Environment Variables

The following environment variables need to be configured in your Lambda function:

- `DB_HOST`: PostgreSQL database host
- `DB_PORT`: PostgreSQL database port (usually 5432)
- `DB_USER`: PostgreSQL database user
- `DB_PASSWORD`: PostgreSQL database password
- `DB_NAME`: PostgreSQL database name
- `OPENAI_API_KEY`: Your OpenAI API key
- `OPENAI_ASSISTANT_ID`: Your OpenAI Assistant ID (optional)
- `FIREBASE_PROJECT_ID`: Your Firebase project ID
- `FIREBASE_PRIVATE_KEY`: Your Firebase private key
- `FIREBASE_CLIENT_EMAIL`: Your Firebase client email

## Testing the Deployment

After deployment, you can test your API using the API Gateway URL:

```bash
curl https://<api-id>.execute-api.<region>.amazonaws.com/prod/
```

You should receive a response like:

```json
{"status":"healthy","message":"Nutrition App API is running"}
```

## Troubleshooting

- **Cold Start Issues**: Lambda functions may experience cold starts. Consider using Provisioned Concurrency for production workloads.
- **Database Connection Issues**: Ensure your Lambda function has proper VPC access to your RDS instance.
- **Timeout Issues**: If your API calls are timing out, increase the Lambda timeout setting.
- **Memory Issues**: If you encounter memory errors, increase the Lambda memory allocation.

## Monitoring and Logging

- CloudWatch Logs: All Lambda function logs are available in CloudWatch Logs
- CloudWatch Metrics: Monitor Lambda function metrics like invocation count, duration, and errors
- X-Ray: Enable X-Ray tracing for detailed request analysis


## Update Lambda
 aws lambda update-function-code \
  --function-name your-lambda-function-name \
  --image-uri your-account-id.dkr.ecr.region.amazonaws.com/nutrition-app:latest