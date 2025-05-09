from fastapi import FastAPI, HTTPException, Path
from pydantic import BaseModel
from typing import List, Optional, Union
from fastapi.middleware.cors import CORSMiddleware
import httpx
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

@app.post("/openai/chat", response_model=ChatResponse)
async def openai_chat(request: ChatRequest):
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")

    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }

    # Build prompt messages here using description
    prompt_content = (
        "Extract the calories, protein (g), carbs (g), fat (g), and sugar (g) from this food description: \""
        + request.description
        + "\". If you can find suitable values, return **only** the result as a JSON object with the following keys: calories, protein, carbs, fat, sugar. "
        + "If the item is a branded product, estimate values based on what you know about that product. If it's unknown, estimate based on a similar generic food. "
        + "If you cannot find suitable values, return a message telling the user what additional information you need. Do not include any explanation."
    )
    messages = [{"role": "user", "content": prompt_content}]

    payload = {
        "model": request.model,
        "messages": messages,
        "temperature": request.temperature,
        "max_tokens": request.max_tokens,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post("https://api.openai.com/v1/chat/completions", json=payload, headers=headers)

    if response.status_code != 200:
        raise HTTPException(status_code=response.status_code, detail=response.text)

    data = response.json()
    print("Raw OpenAI response data:", data)
    content = data['choices'][0]['message']['content'].strip()

    # Try to parse nutritional info from content
    try:
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
