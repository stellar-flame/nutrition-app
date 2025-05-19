from fastapi import APIRouter, Path, Response
from datetime import date, datetime
from crud import get_meals, create_meal, clear_meals
from models import MealCreate, MealResponse

router = APIRouter()

@router.get("/meals/{user_id}")
def get_meals_endpoint(user_id: str = Path(..., description="User ID to fetch meals for"), search_date: str = None):
    if search_date is None:
        search_date = date.today().isoformat()
    rows = get_meals(user_id, search_date)
    meals = []
    for row in rows:
        meals.append({
            "id": row["id"],
            "user_id": row["user_id"],
            "description": row["description"],
            "calories": row["calories"],
            "protein": row["protein"],
            "carbs": row["carbs"],
            "fat": row["fat"],
            "sugar": row["sugar"],
            "timestamp": row["timestamp"],
        })
    return {"meals": meals}

@router.delete("/meals/{user_id}/clear")
def clear_meals_endpoint(user_id: str):
    clear_meals(user_id)
    return Response(content=f"Cleared meals for user {user_id}", status_code=200)

@router.post("/meals/", response_model=MealResponse)
def create_meal_endpoint(meal: MealCreate):
    meal_id, timestamp = create_meal(meal)
    return MealResponse(
        id=meal_id,
        user_id=meal.user_id,
        description=meal.description,
        calories=meal.calories,
        protein=meal.protein,
        carbs=meal.carbs,
        fat=meal.fat,
        sugar=meal.sugar,
        timestamp=timestamp
    )
