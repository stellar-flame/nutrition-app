import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as rds from 'aws-cdk-lib/aws-rds';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import * as ecr from 'aws-cdk-lib/aws-ecr';
import { Platform } from 'aws-cdk-lib/aws-ecr-assets';
import * as path from 'path';

const app = new cdk.App();

const stack = new cdk.Stack(app, 'NutritionAppDockerStack', {
  env: {
    region: 'us-east-1',
  },
});

// Create VPC for RDS (minimal setup)
const vpc = new ec2.Vpc(stack, 'NutritionAppVpc', {
  maxAzs: 2,
  natGateways: 0, // No NAT Gateway to save costs
  subnetConfiguration: [
    {
      cidrMask: 24,
      name: 'Public',
      subnetType: ec2.SubnetType.PUBLIC,
    },
  ],
});

// Create database credentials secret
const dbSecret = new secretsmanager.Secret(stack, 'DatabaseSecret', {
  description: 'RDS PostgreSQL credentials',
  generateSecretString: {
    secretStringTemplate: JSON.stringify({ username: 'postgres' }),
    generateStringKey: 'password',
    excludeCharacters: '"@/\\\'',
  },
});

// Create API keys secret (you'll need to populate these manually)
const apiKeysSecret = new secretsmanager.Secret(stack, 'ApiKeysSecret', {
  description: 'API keys for external services',
  secretStringValue: cdk.SecretValue.unsafePlainText(JSON.stringify({
    openai_api_key: 'your-openai-key-here',
    usda_api_key: 'your-usda-key-here',
    firebase_project_id: 'your-firebase-project-id',
    firebase_private_key: 'your-firebase-private-key',
    firebase_client_email: 'your-firebase-client-email'
  }))
});

// Note: ECR repository is created via GitHub Actions workflow
// We reference an existing repository here
const repositoryUri = `${cdk.Aws.ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/nutrition-app-repo`;

// Create security group for RDS - allow connections from anywhere (for testing)
const dbSecurityGroup = new ec2.SecurityGroup(stack, 'DatabaseSecurityGroup', {
  vpc,
  description: 'Security group for RDS PostgreSQL',
  allowAllOutbound: false,
});

// Allow PostgreSQL connections from anywhere (for testing only)
dbSecurityGroup.addIngressRule(
  ec2.Peer.anyIpv4(),
  ec2.Port.tcp(5432),
  'Allow PostgreSQL connections for testing'
);

// Create RDS PostgreSQL instance in public subnet
const database = new rds.DatabaseInstance(stack, 'NutritionDatabase', {
  engine: rds.DatabaseInstanceEngine.postgres({
    version: rds.PostgresEngineVersion.VER_15,
  }),
  instanceType: ec2.InstanceType.of(ec2.InstanceClass.T3, ec2.InstanceSize.MICRO),
  credentials: rds.Credentials.fromSecret(dbSecret),
  databaseName: 'fast_api_db',
  vpc,
  vpcSubnets: {
    subnetType: ec2.SubnetType.PUBLIC, // Public subnet for testing
  },
  securityGroups: [dbSecurityGroup],
  publiclyAccessible: true, // Allow public access for testing
  allowMajorVersionUpgrade: false,
  autoMinorVersionUpgrade: true,
  backupRetention: cdk.Duration.days(7),
  deletionProtection: false, // Set to true for production
  removalPolicy: cdk.RemovalPolicy.DESTROY, // Change for production
  storageEncrypted: true,
  allocatedStorage: 20,
  maxAllocatedStorage: 100,
});

// Create Lambda function using an image from the ECR repository
const fastApiLambda = new lambda.DockerImageFunction(stack, 'FastApiLambda', {
  code: lambda.DockerImageCode.fromEcr(
    ecr.Repository.fromRepositoryName(stack, 'ExistingRepo', 'nutrition-app-repo'),
    {
      tagOrDigest: 'latest', // Use the 'latest' tag
    }
  ),
  timeout: cdk.Duration.seconds(30),
  memorySize: 512,
  architecture: lambda.Architecture.X86_64,
  environment: {
    // Database connection
    DB_HOST: database.instanceEndpoint.hostname,
    DB_PORT: database.instanceEndpoint.port.toString(),
    DB_NAME: 'fast_api_db',
    DB_USER: 'postgres',
    SQL_ECHO: 'false',
    // API keys secret ARN (fetch at runtime)
    API_KEYS_SECRET_ARN: apiKeysSecret.secretArn,
    ALLOWED_ORIGINS: '*',
  },
});

// Grant Lambda access to the database secret
dbSecret.grantRead(fastApiLambda);

// Grant Lambda access to the API keys secret
apiKeysSecret.grantRead(fastApiLambda);

// Add environment variable for database password from secret
fastApiLambda.addEnvironment('DB_PASSWORD_SECRET_ARN', dbSecret.secretArn);

// Create API Gateway
const api = new apigateway.LambdaRestApi(stack, 'NutritionApi', {
  handler: fastApiLambda,
  proxy: true,
  description: 'Nutrition App API Gateway',
  defaultCorsPreflightOptions: {
    allowOrigins: apigateway.Cors.ALL_ORIGINS,
    allowMethods: apigateway.Cors.ALL_METHODS,
    allowHeaders: ['Content-Type', 'X-Amz-Date', 'Authorization', 'X-Api-Key'],
  },
});

// Output important values
new cdk.CfnOutput(stack, 'ApiUrl', {
  value: api.url,
  description: 'API Gateway URL',
});

new cdk.CfnOutput(stack, 'DatabaseEndpoint', {
  value: database.instanceEndpoint.hostname,
  description: 'RDS Database Endpoint',
});

new cdk.CfnOutput(stack, 'DatabaseSecretArn', {
  value: dbSecret.secretArn,
  description: 'Database credentials secret ARN',
});

new cdk.CfnOutput(stack, 'ApiKeysSecretArn', {
  value: apiKeysSecret.secretArn,
  description: 'API keys secret ARN',
});

new cdk.CfnOutput(stack, 'EcrRepoUri', {
  value: repositoryUri,
  description: 'ECR Repository URI for the Lambda function',
});

// Security warning
new cdk.CfnOutput(stack, 'SecurityNote', {
  value: 'WARNING: RDS is publicly accessible for testing. Secure for production!',
  description: 'Security reminder',
});
