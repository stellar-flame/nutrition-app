from fastapi import APIRouter, HTTPException, Depends
from firebase_admin import auth as firebase_auth
from pydantic import BaseModel
from utils import verify_firebase_token, get_firebase_app
from sqlalchemy.orm import Session
from database.db import get_db
from database.models import UserModel
from datetime import datetime

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
def signup_user(request: SignupRequest, db: Session = Depends(get_db)):
    try:
        # Ensure Firebase is initialized
        get_firebase_app()
        
        # Create user in Firebase
        print(f"Creating user with email: {request.email}")

        user = firebase_auth.create_user(
            email=request.email,
            password=request.password
        )
        
        # Insert user into the database using SQLAlchemy
        # Convert string date to Python date object
        date_of_birth = datetime.strptime(request.date_of_birth, "%Y-%m-%d").date()
        
        # Create UserModel instance
        db_user = UserModel(
            id=user.uid,
            first_name=request.first_name,
            last_name=request.last_name,
            date_of_birth=date_of_birth,
            weight=float(request.weight),
            height=float(request.height)
        )
        
        try:
            # Add to session and commit
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            return {"message": "User created successfully", "uid": user.uid}
        except Exception as db_error:
            db.rollback()
            # Delete the user from Firebase if database insertion fails
            firebase_auth.delete_user(user.uid)
            raise HTTPException(status_code=500, detail=f"Database error: {str(db_error)}")
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
