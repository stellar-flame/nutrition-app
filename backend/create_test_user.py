import sqlite3
from datetime import datetime

DATABASE = "meals.db"

def create_test_user():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (first_name, last_name, date_of_birth, weight, height)
        VALUES (?, ?, ?, ?, ?)
    """, ("Test", "User", "1990-01-01", 70.0, 175.0))
    conn.commit()
    conn.close()
    print("Test user created successfully.")

if __name__ == "__main__":
    create_test_user()
