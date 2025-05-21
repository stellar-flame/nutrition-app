from fastapi import APIRouter, HTTPException, Depends
from firebase_admin import auth as firebase_auth
from pydantic import BaseModel
from utils import verify_firebase_token
import sqlite3

router = APIRouter()

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    id_token: str

class SignupRequest(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str
    date_of_birth: str
    weight: float
    height: float

@router.post("/auth/signup")
def signup_user(request: SignupRequest):
    try:
        # Create user in Firebase
        print(f"Creating user with email: {request.email}")

        user = firebase_auth.create_user(
            email=request.email,
            password=request.password
        )
        
        # Insert user into the database
        conn = sqlite3.connect("meals.db")
        cursor = conn.cursor()
        # Ensure proper type casting before inserting into the database
        cursor.execute(
            """
            INSERT INTO users (id, first_name, last_name, date_of_birth, weight, height)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user.uid,
                request.first_name,
                request.last_name,
                str(request.date_of_birth),  # Cast date_of_birth to string
                float(request.weight),       # Cast weight to float
                float(request.height)        # Cast height to float
            )
        )
        conn.commit()
        conn.close()

        return {"message": "User created successfully", "uid": user.uid}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/auth/login", response_model=LoginResponse)
def login_user(request: LoginRequest):
    raise HTTPException(
        status_code=400,
        detail="Password authentication must be handled on the frontend using Firebase Authentication SDK."
    )

@router.get("/auth/verify")
def verify_user(token: str = Depends(verify_firebase_token)):
    return {"message": "Token is valid", "uid": token}
