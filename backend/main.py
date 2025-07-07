import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database.db import init_db

from api.chat import router as chat_router
from api.meals import router as meals_router
from api.users import router as users_router
from api.auth import router as auth_router

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize database
try:
    init_db()
    logger.info("Database initialized successfully")
except Exception as e:
    logger.error(f"Database initialization failed: {e}")

# Create FastAPI app
app = FastAPI(
    title="Nutrition App API",
    description="API for tracking meals, nutrients, and providing personalized nutrition recommendations",
    version="1.0.0"
)

# Configure CORS
origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat_router)
app.include_router(meals_router)
app.include_router(users_router)
app.include_router(auth_router)

# Root endpoint for health checks
@app.get("/")
def read_root():
    return {"status": "healthy", "message": "Nutrition App API is running"}

@app.get("/health")
def health_check():
    return {
        "status": "healthy", 
        "environment": "lambda" if os.getenv("AWS_LAMBDA_FUNCTION_NAME") else "local",
        "database_host": os.getenv("DB_HOST", "not_set")
    }

# Handler for AWS Lambda
from mangum import Mangum
handler = Mangum(app, lifespan="off")

# Log startup message
logger.info("Nutrition App API initialized and ready to handle requests")
