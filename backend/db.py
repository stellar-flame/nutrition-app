import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL")

# For local development with PostgreSQL as default
if not DATABASE_URL:
    print("Warning: DATABASE_URL not set, using local PostgreSQL database")
    DATABASE_URL = "postgresql://localhost/nutrition_app"
elif DATABASE_URL.startswith("postgres://"):
    # Heroku/Vercel style URLs need to be adapted for SQLAlchemy
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

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
    """Dependency for getting DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize the database (create tables)"""
    Base.metadata.create_all(bind=engine)
