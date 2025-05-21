from fastapi import APIRouter, Path, HTTPException
from math import floor
from crud import create_user_profile, get_user_profile
from models import UserProfile, UserProfileResponse
from utils import calculate_bmr, calculate_age

router = APIRouter()

@router.post("/users/", response_model=UserProfileResponse)
def create_user_profile_endpoint(user: UserProfile):
    user_id = create_user_profile(user)
    return UserProfileResponse(id=user_id, **user.dict())

@router.get("/users/{user_id}", response_model=UserProfileResponse)
def get_user_profile_endpoint(user_id: str = Path(..., description="User UID to fetch profile for")):
    print(f"Fetching user profile for UID: {user_id}")
    row = get_user_profile(user_id)
    if row is None:
        raise HTTPException(status_code=404, detail="User not found")
    return UserProfileResponse(
        id=row["id"],
        first_name=row["first_name"],
        last_name=row["last_name"],
        date_of_birth=row["date_of_birth"],
        weight=row["weight"],
        height=row["height"]
    )

@router.get("/users/{user_id}/nutrition-needs")
def get_nutrition_needs(user_id: str = Path(..., description="User UID to fetch nutrition needs for")):
    row = get_user_profile(user_id)
    if row is None:
        raise HTTPException(status_code=404, detail="User not found")
    age = calculate_age(row["date_of_birth"])
    bmr = calculate_bmr(row["weight"], row["height"], age, sex="male")
    daily_calories = floor(bmr * 1.2)
    protein_g = floor(row["weight"] * 1.2)
    fat_g = floor((daily_calories * 0.25) / 9)
    carbs_g = floor((daily_calories - (protein_g * 4 + fat_g * 9)) / 4)
    sugar_g = floor(carbs_g * 0.1)
    return {
        "calories": daily_calories,
        "protein": protein_g,
        "fat": fat_g,
        "carbs": carbs_g,
        "sugar": sugar_g,
    }
