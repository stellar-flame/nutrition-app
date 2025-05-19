from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from db import init_db
from api.chat import router as chat_router
from api.meals import router as meals_router
from api.users import router as users_router

init_db()

app = FastAPI()

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
