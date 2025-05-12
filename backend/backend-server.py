from fastapi import FastAPI, HTTPException, Path
from math import floor
import datetime as dt
from pydantic import BaseModel
from typing import List, Optional, Union
from fastapi.middleware.cors import CORSMiddleware
import httpx
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage
import os
from dotenv import load_dotenv
import sqlite3
from sqlite3 import Connection
from datetime import datetime
import json
import re

load_dotenv()

app = FastAPI()

# Allow CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

DATABASE = "meals.db"

def get_db_connection() -> Connection:
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS meals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            description TEXT NOT NULL,
            calories REAL NOT NULL,
            protein REAL,
            carbs REAL,
            fat REAL,
            sugar REAL,
            timestamp TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            date_of_birth TEXT NOT NULL,
            weight REAL NOT NULL,
            height REAL NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    user_id: str
    description: str
    # Remove messages from request, prompt will be built in backend
    # messages: List[Message]
    model: Optional[str] = "gpt-4"
    temperature: Optional[float] = 0
    max_tokens: Optional[int] = 150

class UserProfile(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: str  # ISO format date string
    weight: float
    height: float

class UserProfileResponse(UserProfile):
    id: int

class ChatResponse(BaseModel):
    meal: Optional[dict] = None
    clarification: Optional[str] = None

def extract_number(value):
    if isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        match = re.search(r"[-+]?[0-9]*\.?[0-9]+", value)
        if match:
            return float(match.group())
    return 0

def calculate_bmr(weight_kg: float, height_cm: float, age: int, sex: str = "male") -> int:
    """
    Calculate Basal Metabolic Rate (BMR) using Mifflin-St Jeor Equation.
    sex: "male" or "female"
    Returns calories per day.
    """
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

@app.post("/openai/chat", response_model=ChatResponse)
async def openai_chat(request: ChatRequest):
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")

    chat = ChatOpenAI(model_name=request.model, temperature=request.temperature, max_tokens=request.max_tokens)

    prompt_content = (
        "Extract the calories, protein (g), carbs (g), fat (g), and sugar (g) from this food description: \""
        + request.description
        + "\". If you can find suitable values, return **only** the result as a JSON object with the following keys: calories, protein, carbs, fat, sugar. "
        + "If the item is a branded product, estimate values based on what you know about that product. If it's unknown, estimate based on a similar generic food. "
        + "If you cannot find suitable values, return a message telling the user what additional information you need. Do not include any explanation."
    )

    try:
        response = chat.invoke([HumanMessage(content=prompt_content)])
        content = response.content.strip()

        nutrition_raw = json.loads(content)
        # Check if response is clarification message
        if isinstance(nutrition_raw, dict) and "message" in nutrition_raw:
            clarification_msg = nutrition_raw.get("message", "")
            return ChatResponse(clarification=clarification_msg)

        # Otherwise, assume it's the nutrition info
        nutrition = {
            "calories": extract_number(nutrition_raw.get("calories", 0)),
            "protein": extract_number(nutrition_raw.get("protein", 0)),
            "carbs": extract_number(nutrition_raw.get("carbs", 0)),
            "fat": extract_number(nutrition_raw.get("fat", 0)),
            "sugar": extract_number(nutrition_raw.get("sugar", 0)),
        }
        # Store meal in database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO meals (user_id, description, calories, protein, carbs, fat, sugar, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            request.user_id,
            request.description,
            nutrition["calories"],
            nutrition["protein"],
            nutrition["carbs"],
            nutrition["fat"],
            nutrition["sugar"],
            datetime.utcnow().isoformat()
        ))
        conn.commit()
        meal_id = cursor.lastrowid
        conn.close()

        # Return stored meal data
        return ChatResponse(meal={
            "id": meal_id,
            "user_id": request.user_id,
            "description": request.description,
            "calories": nutrition.get("calories", 0),
            "protein": nutrition.get("protein", 0),
            "carbs": nutrition.get("carbs", 0),
            "fat": nutrition.get("fat", 0),
            "sugar": nutrition.get("sugar", 0),
            "timestamp": datetime.utcnow().isoformat()
        })
    except (json.JSONDecodeError, TypeError) as e:
        # If JSON parsing fails, treat content as clarification request
        print(f"JSON parsing error: {e}, content: {content}")
        return ChatResponse(clarification=content)

@app.get("/meals/{user_id}")
def get_meals(user_id: str = Path(..., description="User ID to fetch meals for")):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM meals WHERE user_id = ? ORDER BY timestamp DESC", (user_id,))
    rows = cursor.fetchall()
    conn.close()

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

@app.get("/users/{user_id}/nutrition-needs")
def get_nutrition_needs(user_id: int = Path(..., description="User ID to fetch nutrition needs for")):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail="User not found")

    age = calculate_age(row["date_of_birth"])
    # For simplicity, assume male sex; you can extend UserProfile to include sex if needed
    bmr = calculate_bmr(row["weight"], row["height"], age, sex="male")

    # For now, assume sedentary activity level multiplier 1.2
    daily_calories = floor(bmr * 1.2)

    # Rough macronutrient distribution (grams)
    protein_g = floor(row["weight"] * 1.2)  # 1.2g protein per kg body weight
    fat_g = floor((daily_calories * 0.25) / 9)  # 25% calories from fat, 9 cal/g fat
    carbs_g = floor((daily_calories - (protein_g * 4 + fat_g * 9)) / 4)  # Remaining calories from carbs, 4 cal/g carbs
    sugar_g = floor(carbs_g * 0.1)  # Assume 10% of carbs as sugar

    return {
        "calories": daily_calories,
        "protein": protein_g,
        "fat": fat_g,
        "carbs": carbs_g,
        "sugar": sugar_g,
    }

@app.post("/users/", response_model=UserProfileResponse)
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
    return UserProfileResponse(id=user_id, **user.dict())

@app.get("/users/{user_id}", response_model=UserProfileResponse)
def get_user_profile(user_id: int = Path(..., description="User ID to fetch profile for")):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
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

from fastapi import Response

@app.delete("/meals/{user_id}/clear")
def clear_meals(user_id: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM meals WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    return Response(content=f"Cleared meals for user {user_id}", status_code=200)

# Additional endpoints for stats and recommendations can be added here
