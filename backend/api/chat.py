from fastapi import APIRouter, HTTPException
from openai import OpenAI

from datetime import datetime
import os
from dotenv import load_dotenv
from models import ChatRequest, ChatResponse

router = APIRouter()

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# Define the instructions for the Responses API
ASSISTANT_INSTRUCTIONS = (
    "You are a nutrition assistant. When the user describes a meal, respond using JSON with the following fields:\n\n"
    "{\n"
    '  "intent": "log_food",\n'
    '  "description": string,\n'
    '  "calories": number,\n'
    '  "protein": number,\n'
    '  "fiber": number,\n'
    '  "carbs": number,\n'
    '  "fat": number,\n'
    '  "sugar": number,\n'
    '  "assumptions": string (optional: any assumptions made about portion size, brand, or preparation method)\n'
    "}\n\n"
    "Always fill in numerical values based on your best estimates. "
    "If you cannot estimate a value, respond with using JSON with the following fields:\n\n. "
    "{\n"
    ' "intent": "chat",\n'
    ' "response": "...(explaining why you can\'t estimate the value, e.g., \'Is it whole grain or white bread?\')",\n'
    "}\n\n"
    "Respond with only the JSON block, no extra commentary or explanation."
)


@router.post("/openai/chat", response_model=ChatResponse)
async def openai_chat(request: ChatRequest):
    # Create a new OpenAI client for each request
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    # Build input for Responses API
    input_messages = [
        {
            "role": "user",
            "content": request.description
        }
    ]
    
    # Create response using Responses API with structured outputs
    response_params = {
        "model": "gpt-4o",
        "input": input_messages,
        "instructions": ASSISTANT_INSTRUCTIONS,
        "text": {
            "format": {
                "type": "json_schema",
                "name": "nutrition_response",
                "schema": {
                    "type": "object",
                    "properties": {
                        "intent": {
                            "type": "string", 
                            "enum": ["log_food", "chat"]
                        },
                        "description": {"type": "string"},
                        "calories": {"type": "number"},
                        "protein": {"type": "number"},
                        "fiber": {"type": "number"},
                        "carbs": {"type": "number"},
                        "fat": {"type": "number"},
                        "sugar": {"type": "number"},
                        "assumptions": {"type": "string"},
                        "response": {"type": "string"}
                    },
                    "required": ["intent", "description", "calories", "protein", "fiber", "carbs", "fat", "sugar", "assumptions", "response"],
                    "additionalProperties": False
                }
            }
        }
    }
    
    # Add previous_response_id if continuing conversation
    if request.conversation_id:
        response_params["previous_response_id"] = request.conversation_id
    
    response = client.responses.create(**response_params)
    print(f"OpenAI response: {response}")
    
    # Process the structured response
    if response.output and len(response.output) > 0:
        try:
            # Get the text content from the response
            message = response.output[0]
            if message.content and len(message.content) > 0:
                response_text = message.content[0].text
                # Parse the JSON from the structured output
                import json
                meal_data = json.loads(response_text)
                
                if meal_data.get("intent") == "log_food":
                    # Use structured data directly
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
                    return ChatResponse(
                        meal=nutrition_estimate,
                        conversation_id=response.id,
                    )
                elif meal_data.get("intent") == "chat": 
                    return ChatResponse(
                        message=meal_data.get("response"),
                        conversation_id=response.id,
                    )
                else:
                    return ChatResponse(
                        message="I didn't understand that response. Could you try again?",
                        conversation_id=response.id
                    )
        except Exception as e:
            print(f"Error processing structured response: {e}")
            return ChatResponse(
                message="I had trouble processing the nutrition data. Could you try providing more details?",
                conversation_id=response.id if response else None
            )
    else:   
        print(f"Response failed - no structured output received")
        raise HTTPException(status_code=500, detail="OpenAI response failed")        




