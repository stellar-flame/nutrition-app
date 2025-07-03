"""
Database configuration and connection management.
This module handles database connection setup, session management, and engine configuration.
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get individual database parameters from environment variables
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

# Construct the DATABASE_URL from individual parameters
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Handle empty password case for URL construction
if not DB_PASSWORD:
    DATABASE_URL = f"postgresql://{DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create SQLAlchemy engine with connection pooling for production use
engine = create_engine(
    DATABASE_URL, 
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    # Connection pooling settings
    pool_pre_ping=True,  # Check if connection is alive before using
    pool_recycle=300,    # Recycle connections after 5 minutes
    pool_size=10,        # Maximum number of connections to keep in the pool
    max_overflow=20      # Maximum number of connections that can be created beyond pool_size
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()

def get_db():
    """
    Dependency for getting DB session.
    This is typically used with FastAPI's Depends() for automatic session management.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Initialize the database by creating all tables.
    This should be called once when setting up the application.
    """
    Base.metadata.create_all(bind=engine)

def get_db_session():
    """
    Get a database session for manual session management.
    Remember to close the session when done.
    """
    return SessionLocal()
