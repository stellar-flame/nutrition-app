"""
Lambda-compatible database configuration with AWS Secrets Manager support.
This module handles database connection setup for AWS Lambda environment.
"""
import os
import json
import boto3
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from botocore.exceptions import ClientError

# Create Base class for models
Base = declarative_base()

def get_secret_value(secret_arn):
    """Get secret value from AWS Secrets Manager"""
    try:
        session = boto3.session.Session()
        client = session.client('secretsmanager')
        response = client.get_secret_value(SecretId=secret_arn)
        secret = json.loads(response['SecretString'])
        return secret.get('password')
    except ClientError as e:
        print(f"Error retrieving secret: {e}")
        return None

def get_database_url():
    """Construct database URL with password from Secrets Manager or environment"""
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")
    DB_USER = os.getenv("DB_USER")
    DB_NAME = os.getenv("DB_NAME")
    
    # Try to get password from Secrets Manager first
    secret_arn = os.getenv("DB_PASSWORD_SECRET_ARN")
    if secret_arn:
        DB_PASSWORD = get_secret_value(secret_arn)
    else:
        DB_PASSWORD = os.getenv("DB_PASSWORD")
    
    if not DB_PASSWORD:
        raise ValueError("Database password not found in environment or Secrets Manager")
    
    return f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Initialize database connection
try:
    DATABASE_URL = get_database_url()
    
    # Create SQLAlchemy engine optimized for Lambda
    engine = create_engine(
        DATABASE_URL, 
        echo=os.getenv("SQL_ECHO", "false").lower() == "true",
        # Lambda-optimized connection settings
        pool_pre_ping=True,
        pool_recycle=300,
        pool_size=1,        # Small pool for Lambda
        max_overflow=0,     # No overflow for Lambda
        connect_args={
            "connect_timeout": 10,
            "application_name": "nutrition-app-lambda"
        }
    )
    
    # Create SessionLocal class
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
except Exception as e:
    print(f"Database connection error: {e}")
    # Fallback to original connection for local development
    try:
        from .connection import engine, SessionLocal
    except ImportError:
        print("Could not import fallback connection")
        engine = None
        SessionLocal = None

def get_db():
    """
    Dependency for getting DB session.
    This is typically used with FastAPI's Depends() for automatic session management.
    """
    if SessionLocal is None:
        raise RuntimeError("Database not initialized")
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
    if engine is not None:
        Base.metadata.create_all(bind=engine)

def get_db_session():
    """
    Get a database session for manual session management.
    Remember to close the session when done.
    """
    if SessionLocal is None:
        raise RuntimeError("Database not initialized")
    return SessionLocal()
