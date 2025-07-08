"""Firebase authentication utilities."""

import os
from dotenv import load_dotenv
from firebase_admin import auth as firebase_auth
from fastapi import HTTPException, Header
import firebase_admin
from firebase_admin import credentials
from .secrets import get_secret

# Load environment variables
load_dotenv()

# Global Firebase app instance for serverless optimization
_firebase_app = None

def get_firebase_app():
    """Get Firebase app instance with lazy initialization for serverless"""
    global _firebase_app
    
    if _firebase_app is not None:
        return _firebase_app
    
    try:
        # Check if app is already initialized
        _firebase_app = firebase_admin.get_app()
        return _firebase_app
    except ValueError:
        # Initialize Firebase for the first time
        _firebase_app = _initialize_firebase()
        print("Firebase app initialized successfully")
        return _firebase_app

def _initialize_firebase():
    """Initialize Firebase using secrets from AWS Secrets Manager - internal function"""
    # Get Firebase configuration from secrets
    project_id = get_secret('firebase_project_id')
    private_key = get_secret('firebase_private_key')
    client_email = get_secret('firebase_client_email')
    
    # Fallback to environment variables for local development
    if not project_id:
        project_id = os.getenv("FIREBASE_PROJECT_ID")
    if not private_key:
        private_key = os.getenv("FIREBASE_PRIVATE_KEY")
    if not client_email:
        client_email = os.getenv("FIREBASE_CLIENT_EMAIL")
    
    # Verify required variables
    if not project_id or not private_key or not client_email:
        missing = []
        if not project_id: missing.append("firebase_project_id")
        if not private_key: missing.append("firebase_private_key") 
        if not client_email: missing.append("firebase_client_email")
        raise EnvironmentError(
            f"Missing Firebase configuration: {', '.join(missing)}"
        )
    
    # Handle different escape formats for private key
    if "\\n" in private_key:
        private_key = private_key.replace("\\n", "\n")
    
    # Create credential dict
    cred_dict = {
        "type": os.getenv("FIREBASE_TYPE", "service_account"),
        "project_id": project_id,
        "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
        "private_key": private_key,
        "client_email": client_email,
        "client_id": os.getenv("FIREBASE_CLIENT_ID"),
        "auth_uri": os.getenv("FIREBASE_AUTH_URI", "https://accounts.google.com/o/oauth2/auth"),
        "token_uri": os.getenv("FIREBASE_TOKEN_URI", "https://oauth2.googleapis.com/token"),
        "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_X509_CERT_URL", 
                                                "https://www.googleapis.com/oauth2/v1/certs"),
        "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_X509_CERT_URL")
    }
    
    # Initialize the app with the credentials
    cred = credentials.Certificate(cred_dict)
    return firebase_admin.initialize_app(cred)

def verify_firebase_token(authorization: str = Header(...)) -> str:
    try:
        # Ensure Firebase is initialized
        get_firebase_app()
        
        # Extract the token from the "Bearer <token>" format
        token = authorization.split(" ")[1]
       
        # Verify the token using Firebase Admin SDK
        decoded_token = firebase_auth.verify_id_token(token)
       
        return decoded_token["uid"]  # Return the UID from the decoded token
    except IndexError:
        raise HTTPException(status_code=422, detail="Invalid Authorization header format")
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid Firebase token")
