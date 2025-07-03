"""
SQLAlchemy database models.
This module defines the database schema using SQLAlchemy ORM models.
"""
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.connection import Base


class UserModel(Base):
    """
    User model representing app users.
    Stores user profile information including physical characteristics.
    """
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
    """
    Meal model representing user meal entries.
    Stores nutritional information and meal details.
    """
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
