from fastapi import FastAPI, HTTPException, Path
from math import floor
import datetime as dt
from pydantic import BaseModel
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from langchain_community.chat_message_histories import ChatMessageHistory
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

class ConversationState:
    def __init__(self):
        self.history = ChatMessageHistory()
        self.messages = []
        self.last_activity = datetime.utcnow()

# Store conversations by ID
active_conversations = {}

# Cleanup old conversations (older than 5 minutes)
def cleanup_old_conversations():
    now = datetime.utcnow()
    for conv_id in list(active_conversations.keys()):
        if (now - active_conversations[conv_id].last_activity).total_seconds() > 300:
            del active_conversations[conv_id]

class ChatRequest(BaseModel):
    user_id: str
    description: str
    conversation_id: Optional[str] = None
    user_feedback: Optional[str] = None
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

class MealCreate(BaseModel):
    user_id: str
    description: str
    calories: float
    protein: float
    carbs: float
    fat: float
    sugar: float
    timestamp: Optional[str] = None

class MealResponse(BaseModel):
    id: int
    user_id: str
    description: str
    calories: float
    protein: float
    carbs: float
    fat: float
    sugar: float
    timestamp: str

class ChatResponse(BaseModel):
    meal: Optional[dict] = None
    message: Optional[str] = None  # Generic message field for any non-meal responses
    conversation_complete: Optional[bool] = False
    conversation_id: str

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
 
    # Clean up old conversations
    cleanup_old_conversations()
    
    # Get or create conversation state
    conversation_id = request.conversation_id or datetime.utcnow().isoformat()
    if conversation_id not in active_conversations:
        print('** New  Converstion')
        conversation = ConversationState()
        # Add system message to set context
        conversation.history.add_message(SystemMessage(content=(
            "You are a nutritional assistant. Analyze food descriptions and provide nutritional information. "
            "If you can determine the nutritional information, respond with a JSON object containing: "
            "calories (number), protein (number in grams), carbs (number in grams), fat (number in grams), "
            "sugar (number in grams), description (string). Do not include units in the numbers, just return "
            "the numeric values. Example: {\"calories\": 133, \"protein\": 4, \"carbs\": 25, \"fat\": 1.5, "
            "\"sugar\": 2, \"description\": \"2 slices of white bread\"}. "
            "If you need more information, respond with a normal message asking for what you need."
        )))
        active_conversations[conversation_id] = conversation
    else:
        print('** Ongoing  Converstion')
        
        conversation = active_conversations[conversation_id]
    
    # Update last activity
    conversation.last_activity = datetime.utcnow()
    
    # Add user's message to history
    if request.user_feedback:
        conversation.history.add_user_message(
            f"I previously said: {request.description}\n"
            f"Let me clarify: {request.user_feedback}"
        )
    else:
        conversation.history.add_user_message(request.description)
    
    # Debug: Print conversation history
    print(f"\nConversation {conversation_id} history:")
    for msg in conversation.history.messages:
        print(f"- [{msg.type}]: {msg.content}")
    
    try:
        # Get response using full conversation history
        response = chat.invoke(conversation.history.messages)
        
        # Add AI's response to history
        conversation.history.add_ai_message(response.content)
        content = response.content.strip()

        try:
            print (content)
            
            # Try to parse as nutrition info
            nutrition_raw = json.loads(content)
            print (nutrition_raw)
            nutrition = {
                "calories": extract_number(nutrition_raw.get("calories", 0)),
                "protein": extract_number(nutrition_raw.get("protein", 0)),
                "carbs": extract_number(nutrition_raw.get("carbs", 0)),
                "fat": extract_number(nutrition_raw.get("fat", 0)),
                "sugar": extract_number(nutrition_raw.get("sugar", 0)),
            }
            description_normalized = nutrition_raw.get("description", request.description)

            # Return nutritional information
            return ChatResponse(
                meal={
                    "id": None,  # ID will be assigned when actually storing the meal
                    "user_id": request.user_id,
                    "description": description_normalized,
                    "calories": nutrition.get("calories", 0),
                    "protein": nutrition.get("protein", 0),
                    "carbs": nutrition.get("carbs", 0),
                    "fat": nutrition.get("fat", 0),
                    "sugar": nutrition.get("sugar", 0),
                    "timestamp": datetime.utcnow().isoformat()
                },
                conversation_id=conversation_id
            )
        except json.JSONDecodeError:
            # If not JSON, treat as conversation message
            # If not JSON, treat as conversation message but don't expose raw content
            return ChatResponse(
                message=response.content,
                conversation_id=conversation_id
            )
    except Exception as e:
        print(f"Error processing request: {e}")
        return ChatResponse(
            message="I couldn't process that. Could you try rephrasing?",
            conversation_id=conversation_id
        )

from datetime import date

@app.get("/meals/{user_id}")
def get_meals(user_id: str = Path(..., description="User ID to fetch meals for"), search_date: str = None):
    """
    Get meals for a user, optionally filtered by date (YYYY-MM-DD).
    Defaults to today's date if no date is provided.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    print("Search Date: ", search_date)
    if search_date is None:
        search_date = date.today().isoformat()
    cursor.execute("SELECT * FROM meals WHERE user_id = ? AND date(timestamp) = ? ORDER BY timestamp DESC", (user_id, search_date))
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

@app.post("/meals/", response_model=MealResponse)
def create_meal(meal: MealCreate):
    """
    Create a new meal entry in the database.
    This endpoint handles the actual storage of meal data, separate from the OpenAI chat functionality.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Use current date if timestamp not provided
    timestamp = meal.timestamp or datetime.utcnow().date().isoformat()
    
    try:
        cursor.execute("""
            INSERT INTO meals (user_id, description, calories, protein, carbs, fat, sugar, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            meal.user_id,
            meal.description,
            meal.calories,
            meal.protein,
            meal.carbs,
            meal.fat,
            meal.sugar,
            timestamp
        ))
        conn.commit()
        meal_id = cursor.lastrowid
        
        # Return the created meal with its ID
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
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# Additional endpoints for stats and recommendations can be added here
