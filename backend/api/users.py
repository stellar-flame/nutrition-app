from fastapi import APIRouter, Path, HTTPException, Depends
from sqlalchemy.orm import Session
from math import floor
from database.crud import create_user_profile, get_user_profile, update_user_profile
from database.schemas import UserProfile, UserProfileResponse
from utils import calculate_bmr, calculate_age
from database.db import get_db

router = APIRouter()

@router.post("/users/", response_model=UserProfileResponse)
def create_user_profile_endpoint(user: UserProfile, db: Session = Depends(get_db)):
    user_id = create_user_profile(user, db)
    return UserProfileResponse(id=user_id, **user.model_dump())

@router.get("/users/{user_id}", response_model=UserProfileResponse)
def get_user_profile_endpoint(user_id: str = Path(..., description="User UID to fetch profile for"), 
                             db: Session = Depends(get_db)):
    print(f"Fetching user profile for UID: {user_id}")
    db_user = get_user_profile(user_id, db)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    # With SQLAlchemy models, we can directly return the model instance
    print(f"User profile found: {db_user}")
    # Explicitly create UserProfileResponse
    return db_user
    

@router.get("/users/{user_id}/nutrition-needs")
def get_nutrition_needs(
    user_id: str = Path(..., description="User UID to fetch nutrition needs for"), 
    gender: str = "male",
    db: Session = Depends(get_db)
):
    user = get_user_profile(user_id, db)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    age = calculate_age(user.date_of_birth)
    bmr = calculate_bmr(user.weight, user.height, age, sex=gender)
    daily_calories = floor(bmr * 1.2)
    protein_g = floor(user.weight * 1.2)

    fiber_g = floor(daily_calories * 0.014)  # 14g fiber per 1,000 calories
    
    fat_g = floor((daily_calories * 0.25) / 9)
    carbs_g = floor((daily_calories - (protein_g * 4 + fat_g * 9)) / 4)
    sugar_g = floor(carbs_g * 0.1)
    return {
        "calories": daily_calories,
        "protein": protein_g,
        "fiber": fiber_g,
        "fat": fat_g,
        "carbs": carbs_g,
        "sugar": sugar_g,
    }
