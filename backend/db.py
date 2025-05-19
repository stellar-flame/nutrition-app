import sqlite3
from sqlite3 import Connection

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
