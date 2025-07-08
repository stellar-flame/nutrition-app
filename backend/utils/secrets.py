"""
AWS Secrets Manager helper for fetching API keys at runtime.
"""
import json
import os
import boto3
from functools import lru_cache
from typing import Dict, Any

# Initialize AWS clients
secrets_client = boto3.client('secretsmanager')

@lru_cache(maxsize=1)
def get_api_keys() -> Dict[str, str]:
    """
    Fetch API keys from AWS Secrets Manager.
    Cached to avoid repeated API calls.
    """
    secret_arn = os.getenv('API_KEYS_SECRET_ARN')
    if not secret_arn:
        print("⚠️  API_KEYS_SECRET_ARN not found, using fallback values")
        return {
            'openai_api_key': os.getenv('OPENAI_API_KEY', ''),
            'usda_api_key': os.getenv('USDA_API_KEY', ''),
            'firebase_project_id': os.getenv('FIREBASE_PROJECT_ID', ''),
            'firebase_private_key': os.getenv('FIREBASE_PRIVATE_KEY', ''),
            'firebase_client_email': os.getenv('FIREBASE_CLIENT_EMAIL', '')
        }
    
    try:
        response = secrets_client.get_secret_value(SecretId=secret_arn)
        secret_data = json.loads(response['SecretString'])
        print("✅ Successfully loaded API keys from Secrets Manager")
        return secret_data
    except Exception as e:
        print(f"❌ Failed to load secrets: {e}")
        # Fallback to environment variables
        return {
            'openai_api_key': os.getenv('OPENAI_API_KEY', ''),
            'usda_api_key': os.getenv('USDA_API_KEY', ''),
            'firebase_project_id': os.getenv('FIREBASE_PROJECT_ID', ''),
            'firebase_private_key': os.getenv('FIREBASE_PRIVATE_KEY', ''),
            'firebase_client_email': os.getenv('FIREBASE_CLIENT_EMAIL', '')
        }

def get_secret(key: str) -> str:
    """Get a specific secret value by key."""
    secrets = get_api_keys()
    return secrets.get(key, '')
