from fastapi import APIRouter, HTTPException
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage
from langchain_community.chat_message_histories import ChatMessageHistory
from datetime import datetime
import os
import json
import re
from dotenv import load_dotenv
from models import ChatRequest, ChatResponse
from utils import extract_number

router = APIRouter()

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

active_conversations = {}

class ConversationState:
    def __init__(self):
        self.history = ChatMessageHistory()
        self.last_activity = datetime.utcnow()

def cleanup_old_conversations():
    now = datetime.utcnow()
    for conv_id in list(active_conversations.keys()):
        if (now - active_conversations[conv_id].last_activity).total_seconds() > 300:
            del active_conversations[conv_id]

@router.post("/openai/chat", response_model=ChatResponse)
async def openai_chat(request: ChatRequest):
    if not OPENAI_API_KEY:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")
    chat = ChatOpenAI(model_name=request.model, temperature=request.temperature, max_tokens=request.max_tokens)
    cleanup_old_conversations()
    conversation_id = request.conversation_id or datetime.utcnow().isoformat()
    if conversation_id not in active_conversations:
        conversation = ConversationState()
        conversation.history.add_message(SystemMessage(content=(
            "You are a nutritional assistant. Analyze food descriptions and provide estimated nutritional information, even if details are limited. "
            "If you can determine or reasonably assume the nutritional content, respond with a JSON object containing: "
            "calories (number), protein (number in grams), carbs (number in grams), fat (number in grams), sugar (number in grams), "
            "description (string), assumptions (string). Do not include units in the numbers, just return numeric values. "
            "Example: {\"calories\": 133, \"protein\": 4, \"carbs\": 25, \"fat\": 1.5, \"sugar\": 2, \"description\": \"2 slices of white bread\", \"assumptions\": \"50g slice\"}. "
            "Keep 'assumptions' short. If the item is from a restaurant or brand, use typical serving sizes and similar foods to estimate. "
            "If absolutely no assumptions can be made, only then ask for clarification. Keep any explanations short and sweet."
        )))
        active_conversations[conversation_id] = conversation
    else:
        conversation = active_conversations[conversation_id]
    conversation.last_activity = datetime.utcnow()
    if request.user_feedback:
        conversation.history.add_user_message(
            f"I previously said: {request.description}\nLet me clarify: {request.user_feedback}"
        )
    else:
        conversation.history.add_user_message(request.description)
    try:
        response = chat.invoke(conversation.history.messages)
        conversation.history.add_ai_message(response.content)
        content = response.content.strip()
        try:
            match = re.search(r"(\{.*?\})", content, re.DOTALL)
            if not match:
                raise ValueError("No JSON block found")
            json_text = match.group(1)
            nutrition_raw = json.loads(json_text)
            nutrition = {
                "calories": extract_number(nutrition_raw.get("calories", 0)),
                "protein": extract_number(nutrition_raw.get("protein", 0)),
                "carbs": extract_number(nutrition_raw.get("carbs", 0)),
                "fat": extract_number(nutrition_raw.get("fat", 0)),
                "sugar": extract_number(nutrition_raw.get("sugar", 0)),
            }
            description_normalized = nutrition_raw.get("description", request.description)
            assumptions_normalized = nutrition_raw.get("assumptions")
            return ChatResponse(
                meal={
                    "id": None,
                    "user_id": request.user_id,
                    "description": description_normalized,
                    "assumptions": assumptions_normalized,
                    "calories": nutrition["calories"],
                    "protein": nutrition["protein"],
                    "carbs": nutrition["carbs"],
                    "fat": nutrition["fat"],
                    "sugar": nutrition["sugar"],
                    "timestamp": datetime.utcnow().isoformat()
                },
                conversation_id=conversation_id
            )
        except (ValueError, json.JSONDecodeError):
            return ChatResponse(
                message=content,
                meal=None,
                conversation_id=conversation_id
            )
    except Exception:
        return ChatResponse(
            message="I couldn't process that. Could you try rephrasing?",
            conversation_id=conversation_id
        )
