from fastapi import APIRouter, Path, Response, HTTPException, Depends
from datetime import date, datetime
from sqlalchemy.orm import Session
from crud import get_meals, create_meal, clear_meals, delete_meal as crud_delete_meal, get_meal
from models import MealCreate, MealResponse
from db import get_db

router = APIRouter()

@router.get("/meals/{user_id}")
def get_meals_endpoint(
    user_id: str = Path(..., description="User ID to fetch meals for"), 
    search_date: str = None,
    db: Session = Depends(get_db)
):
    if search_date is None:
        search_date = date.today().isoformat()
    
    meals = get_meals(user_id, search_date, db)
    # SQLAlchemy objects are returned with all their attributes
    return {"meals": meals}

@router.delete("/meals/{user_id}/clear")
def clear_meals_endpoint(user_id: str, db: Session = Depends(get_db)):
    deleted_count = clear_meals(user_id, db)
    return Response(content=f"Cleared {deleted_count} meals for user {user_id}", status_code=200)

@router.post("/meals/", response_model=MealResponse)
def create_meal_endpoint(meal: MealCreate, db: Session = Depends(get_db)):
    db_meal, timestamp = create_meal(meal, db)
    return db_meal

@router.delete("/meals/{meal_id}")
def delete_meal_endpoint(meal_id: int, db: Session = Depends(get_db)):
    meal = get_meal(meal_id, db)
    if not meal:
        raise HTTPException(status_code=404, detail="Meal not found")
    
    deleted = crud_delete_meal(meal_id, db)
    if not deleted:
        raise HTTPException(status_code=500, detail="Failed to delete meal")
    
    return Response(content=f"Deleted meal {meal_id}", status_code=200)
