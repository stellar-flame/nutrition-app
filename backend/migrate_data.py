#!/usr/bin/env python3
"""
Script to migrate data from SQLite to PostgreSQL.
"""
import sqlite3
import os
from datetime import datetime
from sqlalchemy.orm import Session
from db import SessionLocal, init_db
from models import UserModel, MealModel

def migrate_data():
    """
    Migrate data from SQLite to PostgreSQL.
    """
    print("Starting migration from SQLite to PostgreSQL...")
    # Connect to SQLite database
    sqlite_conn = sqlite3.connect("meals.db")
    sqlite_conn.row_factory = sqlite3.Row
    
    # Create a session for PostgreSQL
    pg_session = SessionLocal()
    
    try:
        # Migrate users
        print("Migrating users...")
        sqlite_cursor = sqlite_conn.cursor()
        sqlite_cursor.execute("SELECT * FROM users")
        users = sqlite_cursor.fetchall()
        
        for user in users:
            # Convert date string to Python date
            date_of_birth = datetime.strptime(user["date_of_birth"], "%Y-%m-%d").date()
            
            # Create user in PostgreSQL
            pg_user = UserModel(
                id=user["id"],
                first_name=user["first_name"],
                last_name=user["last_name"],
                date_of_birth=date_of_birth,
                weight=user["weight"],
                height=user["height"]
            )
            pg_session.add(pg_user)
        
        # Commit users first
        pg_session.commit()
        print(f"Migrated {len(users)} users")
        
        # Migrate meals
        print("Migrating meals...")
        sqlite_cursor.execute("SELECT * FROM meals")
        meals = sqlite_cursor.fetchall()
        
        for meal in meals:
            # Convert timestamp string to datetime
            try:
                timestamp = datetime.fromisoformat(meal["timestamp"].replace("Z", "+00:00"))
            except ValueError:
                # Handle case where timestamp might be in a different format
                timestamp = datetime.strptime(meal["timestamp"], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=None)
            
            # Create meal in PostgreSQL
            pg_meal = MealModel(
                id=meal["id"],  # Keep the same ID
                user_id=meal["user_id"],
                description=meal["description"],
                calories=meal["calories"],
                protein=meal["protein"] or 0,
                fiber=meal["fiber"] or 0,
                carbs=meal["carbs"] or 0,
                fat=meal["fat"] or 0,
                sugar=meal["sugar"] or 0,
                assumptions=None,  # New field, not in SQLite
                timestamp=timestamp
            )
            pg_session.add(pg_meal)
        
        # Commit meals
        pg_session.commit()
        print(f"Migrated {len(meals)} meals")
        
        print("Migration completed successfully!")
        
    except Exception as e:
        pg_session.rollback()
        print(f"Error during migration: {str(e)}")
    finally:
        pg_session.close()
        sqlite_conn.close()

if __name__ == "__main__":
    # Ensure database tables are created
    init_db()
    migrate_data()
