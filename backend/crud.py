from db import get_db_connection
from models import MealCreate, UserProfile
from datetime import datetime
from fastapi import HTTPException

# CRUD for meals

def create_meal(meal: MealCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    timestamp = meal.timestamp or datetime.utcnow().date().isoformat()
    try:
        cursor.execute("""
            INSERT INTO meals (user_id, description, calories, protein, fiber, carbs, fat, sugar, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            meal.user_id,
            meal.description,
            meal.calories,
            meal.protein,
            meal.fiber,
            meal.carbs,
            meal.fat,
            meal.sugar,
            timestamp
        ))
        conn.commit()
        meal_id = cursor.lastrowid
        return meal_id, timestamp
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

def get_meals(user_id: str, search_date: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM meals WHERE user_id = ? AND date(timestamp) = ? ORDER BY timestamp DESC", (user_id, search_date))
    rows = cursor.fetchall()
    conn.close()
    return rows

def clear_meals(user_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM meals WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def create_user_profile(user: UserProfile):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (first_name, last_name, date_of_birth, weight, height)
        VALUES (?, ?, ?, ?, ?)
    """, (user.first_name, user.last_name, user.date_of_birth, user.weight, user.height))
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return user_id

def get_user_profile(user_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row
