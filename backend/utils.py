from math import floor
import datetime as dt
import re
import os
from dotenv import load_dotenv
from firebase_admin import auth as firebase_auth
from fastapi import HTTPException, Header
import firebase_admin
from firebase_admin import credentials

# Load environment variables
load_dotenv()

def initialize_firebase():
    """Initialize Firebase using environment variables only"""
    try:
        # Check if app is already initialized
        firebase_admin.get_app()
        print("Firebase already initialized")
    except ValueError:
        # Verify required environment variables
        required_vars = ["FIREBASE_PROJECT_ID", "FIREBASE_PRIVATE_KEY", "FIREBASE_CLIENT_EMAIL"]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            raise EnvironmentError(
                f"Missing required Firebase environment variables: {', '.join(missing_vars)}. "
                "Please set these in your .env file."
            )
        
        # Create credential dict from environment variables
        cred_dict = {
            "type": os.getenv("FIREBASE_TYPE", "service_account"),
            "project_id": os.getenv("FIREBASE_PROJECT_ID"),
            "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
            "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace("\\n", "\n"),
            "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
            "client_id": os.getenv("FIREBASE_CLIENT_ID"),
            "auth_uri": os.getenv("FIREBASE_AUTH_URI", "https://accounts.google.com/o/oauth2/auth"),
            "token_uri": os.getenv("FIREBASE_TOKEN_URI", "https://oauth2.googleapis.com/token"),
            "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_X509_CERT_URL", 
                                                    "https://www.googleapis.com/oauth2/v1/certs"),
            "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_X509_CERT_URL")
        }
        
        # Initialize the app with the credentials
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred)
        print("Firebase initialized using environment variables")

# Initialize Firebase on module load
initialize_firebase()

def extract_number(value):
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        match = re.search(r"[-+]?[0-9]*\.?[0-9]+", value)
        if match:
            return float(match.group())
    return 0

def calculate_bmr(weight_kg: float, height_cm: float, age: int, sex: str = "male") -> int:
    if sex.lower() == "male":
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
    return floor(bmr)

def calculate_age(dob) -> int:
    today = dt.date.today()
    age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
    return age

def verify_firebase_token(authorization: str = Header(...)) -> str:
    try:
        # Extract the token from the "Bearer <token>" format
        token = authorization.split(" ")[1]
       
        # Verify the token using Firebase Admin SDK
        decoded_token = firebase_auth.verify_id_token(token)
       
        return decoded_token["uid"]  # Return the UID from the decoded token
    except IndexError:
        raise HTTPException(status_code=422, detail="Invalid Authorization header format")
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid Firebase token")
