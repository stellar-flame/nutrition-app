from pydantic import BaseModel
from typing import Optional

class Message(BaseModel):
    role: str
    content: str

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
    assumptions: Optional[str] = None
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
