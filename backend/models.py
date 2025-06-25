from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db import Base

# SQLAlchemy Models
class UserModel(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    date_of_birth = Column(Date, nullable=False)
    weight = Column(Float, nullable=False)  # in kg
    height = Column(Float, nullable=False)  # in cm
    
    # Relationships
    meals = relationship("MealModel", back_populates="user", cascade="all, delete-orphan")

class MealModel(Base):
    __tablename__ = "meals"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    description = Column(String, nullable=False)
    calories = Column(Float, nullable=False)
    protein = Column(Float, nullable=False)
    fiber = Column(Float, nullable=False)
    carbs = Column(Float, nullable=False)
    fat = Column(Float, nullable=False)
    sugar = Column(Float, nullable=False)
    assumptions = Column(Text, nullable=True)
    meal_date = Column(Date, nullable=False)
    timestamp = Column(DateTime, server_default=func.now())
    
    # Relationships
    user = relationship("UserModel", back_populates="meals")

# Pydantic Models
class Message(BaseModel):
    role: str
    content: str
    
    model_config = ConfigDict(from_attributes=True)

class ChatRequest(BaseModel):
    user_id: str
    description: str
    conversation_id: Optional[str] = None
    user_feedback: Optional[str] = None
    model: Optional[str] = "gpt-4"
    temperature: Optional[float] = 0
    max_tokens: Optional[int] = 150
    
    model_config = ConfigDict(from_attributes=True)

class UserProfile(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: date  # Now using Python date type
    weight: float
    height: float
    
    model_config = ConfigDict(from_attributes=True)

class UserProfileResponse(UserProfile):
    id: str
    model_config = ConfigDict(from_attributes=True)

class MealCreate(BaseModel):
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

class ChatResponse(BaseModel):
    meal: Optional[Dict[str, Any]] = None
    message: Optional[str] = None  # Generic message field for any non-meal responses
    conversation_complete: Optional[bool] = False
    conversation_id: str
    
    model_config = ConfigDict(from_attributes=True)
