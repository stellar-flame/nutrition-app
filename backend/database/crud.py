from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date
from database.models import MealModel, UserModel
from database.schemas import MealCreate, UserProfile
from datetime import datetime
import uuid
from fastapi import HTTPException
from typing import List, Optional, Tuple

# CRUD for meals

def create_meal(meal: MealCreate, db: Session) -> Tuple[MealModel, datetime]:
    """Create a new meal entry using SQLAlchemy"""
    try:
        db_meal = MealModel(
            user_id=meal.user_id,
            description=meal.description,
            calories=meal.calories,
            protein=meal.protein,
            fiber=meal.fiber,
            carbs=meal.carbs,
            fat=meal.fat,
            sugar=meal.sugar,
            assumptions=meal.assumptions,
            meal_date=meal.meal_date
        )
        db.add(db_meal)
        db.commit()
        db.refresh(db_meal)
        return db_meal, db_meal.timestamp
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create meal: {str(e)}")

def get_meals(user_id: str, search_date: str, db: Session) -> List[MealModel]:
    """Get all meals for a user on a specific date"""
    # Convert string date to datetime object for comparison
    date_obj = datetime.strptime(search_date, '%Y-%m-%d').date()
    
    # Query all meals for the user on the given date
    meals = db.query(MealModel).filter(
        MealModel.user_id == user_id,
        func.date(MealModel.meal_date) == date_obj
    ).order_by(MealModel.timestamp.desc()).all()
    
    return meals

def get_meal(meal_id: int, db: Session) -> Optional[MealModel]:
    """Get a specific meal by ID"""
    return db.query(MealModel).filter(MealModel.id == meal_id).first()

def delete_meal(meal_id: int, db: Session) -> bool:
    """Delete a meal by ID"""
    meal = db.query(MealModel).filter(MealModel.id == meal_id).first()
    if meal:
        db.delete(meal)
        db.commit()
        return True
    return False

def clear_meals(user_id: str, db: Session) -> int:
    """Delete all meals for a user and return the count of deleted meals"""
    result = db.query(MealModel).filter(MealModel.user_id == user_id).delete()
    db.commit()
    return result

def create_user_profile(user: UserProfile, db: Session) -> str:
    """Create a new user profile"""
    # Generate a UUID for the user ID
    user_id = str(uuid.uuid4())
    
    db_user = UserModel(
        id=user_id,
        first_name=user.first_name,
        last_name=user.last_name,
        date_of_birth=user.date_of_birth,
        weight=user.weight,
        height=user.height
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user.id

def get_user_profile(user_id: str, db: Session) -> Optional[UserModel]:
    """Get a user profile by ID"""
    return db.query(UserModel).filter(UserModel.id == user_id).first()

def update_user_profile(user_id: str, user: UserProfile, db: Session) -> Optional[UserModel]:
    """Update an existing user profile"""
    db_user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if db_user:
        db_user.first_name = user.first_name
        db_user.last_name = user.last_name
        db_user.date_of_birth = user.date_of_birth
        db_user.weight = user.weight
        db_user.height = user.height
        
        db.commit()
        db.refresh(db_user)
        return db_user
    return None
