from fastapi import APIRouter, HTTPException
from langchain_openai import ChatOpenAI

from langchain.schema import SystemMessage, HumanMessage, AIMessage
from langchain.schema.messages import BaseMessage

from datetime import datetime
import os
import json
from dotenv import load_dotenv
from models import ChatRequest, ChatResponse

router = APIRouter()

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

active_conversations = {}



class ConversationState:
    def __init__(self):
        self.history: list[BaseMessage] = []
        self.last_activity: datetime = datetime.utcnow()

    def add_message(self, msg: BaseMessage):
        self.history.append(msg)

    def add_user(self, content: str):
        self.add_message(HumanMessage(content=content))

    def add_system(self, content: str):
        self.add_message(SystemMessage(content=content))

    def add_ai(self, content: str):
        self.add_message(AIMessage(content=content))

# --- Define the function schema for OpenAI ---
nutrition_function = {
    "name": "extract_nutrition",
    "description": "Estimate nutrition data from a food description. Always include numerical values for all nutritional fields.",
    "parameters": {
        "type": "object",
        "properties": {
            "calories": {
                "type": "number",
                "description": "Estimated calories in the food item"
            },
            "protein": {
                "type": "number", 
                "description": "Protein content in grams"
            },
            "fiber": {
                "type": "number",
                "description": "Dietary fiber in grams"
            }, 
            "carbs": {
                "type": "number",
                "description": "Total carbohydrates in grams"
            },
            "fat": {
                "type": "number",
                "description": "Total fat content in grams"
            },
            "sugar": {
                "type": "number",
                "description": "Sugar content in grams"
            },
            "description": {
                "type": "string",
                "description": "Normalized food description"
            },
            "assumptions": {
                "type": "string",
                "description": "Any assumptions made about portion size, brand, or preparation method"
            },
        },
        "required": ["calories", "protein", "fiber", "carbs", "fat", "sugar", "description"]
    }
}


def cleanup_old_conversations():
    now = datetime.now()
    for conv_id in list(active_conversations.keys()):
        if (now - active_conversations[conv_id].last_activity).total_seconds() > 300:
            del active_conversations[conv_id]

@router.post("/openai/chat", response_model=ChatResponse)
async def openai_chat(request: ChatRequest):
    chat = ChatOpenAI(
        model_name=request.model,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
        openai_api_key=OPENAI_API_KEY,  # Ideally use env var
        request_timeout=30,
        model_kwargs={"tools": [{"type": "function", "function": nutrition_function}]},
        streaming=False
    )

    conversation_id = request.conversation_id or datetime.utcnow().isoformat()
    conversation = active_conversations.get(conversation_id, ConversationState())

    if not conversation.history:
        conversation.add_system((
            "You are a nutritional assistant. Use the extract_nutrition function when estimating values. "
            "Always provide numeric values for calories, protein, carbs, fat, sugar, and fiber. "
            "Make reasonable estimations based on standard portions when specifics aren't provided. "
            "Respond concisely and only ask for clarification if absolutely needed."
            "Any assumptions made about portion size, brand, or preparation method should be included in the assumptions.\n\n"
            "\n\nALWAYS USE THE extract_nutrition FUNCTION to process food descriptions."
        ))

    content = (
        f"I previously said: {request.description}\nLet me clarify: {request.user_feedback}"
        if request.user_feedback else request.description
    )
    conversation.add_user(content)
    conversation.last_activity = datetime.utcnow()

    try:
        try:
            response = chat.invoke(conversation.history)
            conversation.add_ai(response.content or "")
        except Exception as e:
            print(f"Error during chat.invoke: {e}")
            raise

        tool_calls = getattr(response, "tool_calls", [])
        print(f"Tool calls: {tool_calls}")
        
        if not tool_calls:
            return ChatResponse(
                message=response.content.strip(),
                conversation_id=conversation_id
            )

        # Handle different response structures
        try:
            meal_data = tool_calls[0]['args'] 
            print(f"Extracted meal data: {meal_data}")
            
            # Ensure all required fields are present with default values
            nutrition_estimate = {
                "id": None,  # ID will be set later when saving to DB
                "user_id": request.user_id,
                "timestamp": datetime.now().isoformat(),
                "calories": meal_data.get("calories", 0),   
                "protein": meal_data.get("protein", 0),
                "fiber": meal_data.get("fiber", 0),     
                "carbs": meal_data.get("carbs", 0),
                "fat": meal_data.get("fat", 0),
                "sugar": meal_data.get("sugar", 0),
                "description": meal_data.get("description", request.description),
                "assumptions": meal_data.get("assumptions", None)
            }
            

            active_conversations[conversation_id] = conversation

            return ChatResponse(meal=nutrition_estimate, conversation_id=conversation_id)
        except Exception as e:
            print(f"Error processing tool call data: {e}")
            return ChatResponse(
                message="I had trouble processing the nutrition data. Could you try providing more details?",
                conversation_id=conversation_id
            )

    except Exception as e:
        print(f"Error processing conversation {conversation_id}: {e}")
        return ChatResponse(
            message="I couldn’t process that. Could you try rephrasing?",
            conversation_id=conversation_id
        )