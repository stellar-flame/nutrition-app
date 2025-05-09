import os

db_path = "meals.db"

if os.path.exists(db_path):
    os.remove(db_path)
    print(f"Deleted database file: {db_path}")
else:
    print(f"Database file not found: {db_path}")
