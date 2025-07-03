"""
Pydantic schemas for API request/response validation.
This module defines the data validation and serialization models used by the API endpoints.
"""
from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import date, datetime


class Message(BaseModel):
    """Basic message structure for chat/conversation contexts."""
    role: str
    content: str
    
    model_config = ConfigDict(from_attributes=True)


class ChatRequest(BaseModel):
    """Request model for chat/meal analysis endpoints."""
    user_id: str
    description: str
    conversation_id: Optional[str] = None
    user_feedback: Optional[str] = None
    model: Optional[str] = "gpt-4"
    temperature: Optional[float] = 0
    max_tokens: Optional[int] = 150
    
    model_config = ConfigDict(from_attributes=True)


class ChatResponse(BaseModel):
    """Response model for chat/meal analysis endpoints."""
    meals: Optional[List[Dict[str, Any]]] = None
    message: Optional[str] = None  # Generic message field for any non-meal responses
    conversation_complete: Optional[bool] = False
    conversation_id: str
    
    model_config = ConfigDict(from_attributes=True)


class StepResponse(BaseModel):
    """Standardized response model for LLM workflow steps."""
    success: bool
    response_id: str
    tool_call_id: Optional[str] = None
    error_message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(from_attributes=True)


class UserProfile(BaseModel):
    """User profile data for creation/updates."""
    first_name: str
    last_name: str
    date_of_birth: date
    weight: float  # in kg
    height: float  # in cm
    
    model_config = ConfigDict(from_attributes=True)


class UserProfileResponse(UserProfile):
    """User profile response including the user ID."""
    id: str
    model_config = ConfigDict(from_attributes=True)


class MealCreate(BaseModel):
    """Model for creating new meal entries."""
    user_id: str
    description: str
    calories: float
    fiber: float
    protein: float
    carbs: float
    fat: float
    sugar: float
    meal_date: date
    timestamp: Optional[datetime] = None
    assumptions: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class MealResponse(BaseModel):
    """Model for meal data responses."""
    id: int
    user_id: str
    description: str
    assumptions: Optional[str] = None
    calories: float
    protein: float
    fiber: float
    carbs: float
    fat: float
    sugar: float
    meal_date: date
    timestamp: datetime
    
    model_config = ConfigDict(from_attributes=True)
