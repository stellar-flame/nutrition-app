from math import floor
import datetime as dt
import re
from firebase_admin import auth as firebase_auth
from fastapi import HTTPException, Header
import firebase_admin
from firebase_admin import credentials

# Initialize Firebase Admin SDK
cred = credentials.Certificate("firebase-credentials/serviceAccountKey.json")
firebase_admin.initialize_app(cred)

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

def calculate_age(dob_str: str) -> int:
    dob = dt.datetime.strptime(dob_str, "%Y-%m-%d").date()
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
