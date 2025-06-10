from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from db import init_db
from api.chat import router as chat_router
from api.meals import router as meals_router
from api.users import router as users_router
from api.auth import router as auth_router

init_db()

app = FastAPI(
    title="Nutrition App API",
    description="API for tracking meals, nutrients, and providing personalized nutrition recommendations",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(meals_router)
app.include_router(users_router)
app.include_router(auth_router)

# Root endpoint for health checks
@app.get("/")
def read_root():
    return {"status": "healthy", "message": "Nutrition App API is running"}

# Handler for serverless functions (Vercel)
from mangum import Mangum
handler = Mangum(app)
