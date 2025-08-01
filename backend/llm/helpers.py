"""
OpenAI helper functions and utilities for the nutrition app.
"""
from openai import OpenAI
from database.schemas import ChatResponse
import re


async def create_openai_response(client: OpenAI, model: str, messages, instructions: str,  tools: list = None) -> object:
    """Standardized OpenAI response creation"""
    
    # Create the system message with instructions
    system_message = {"role": "system", "content": instructions}
    
    # Combine system message with user messages
    all_messages = [system_message] + (messages if isinstance(messages, list) else [messages])
    
    params = {
        "model": model,
        "messages": all_messages
    }
    
    if tools:
        params["tools"] = tools
        params["tool_choice"] = "auto"

    return client.chat.completions.create(**params)


def create_error_response(message: str, conversation_id: str) -> ChatResponse:
    """Standardized error response creation"""
    return ChatResponse(
        message=message,
        conversation_id=conversation_id
    )


def extract_response_text(response) -> str:
    """Extract and clean text from OpenAI response"""
    if hasattr(response, 'choices') and response.choices:
        return response.choices[0].message.content.strip()
    return ""


def clean_json_text(text: str) -> str:
    """Remove markdown code blocks from JSON text"""
    clean_text = text.strip()
    clean_text = re.sub(r'^```json\s*', '', clean_text)
    clean_text = re.sub(r'^```\s*', '', clean_text)
    clean_text = re.sub(r'\s*```$', '', clean_text)
    return clean_text.strip()


def filter_usda_json(usda_data: dict) -> dict:
    """Filter USDA JSON to essential fields only to reduce token usage"""
    filtered = {
        "description": usda_data.get("description", ""),
        "fdcId": usda_data.get("fdcId", ""),
        "dataType": usda_data.get("dataType", ""),
        "servingSize": usda_data.get("servingSize"),
        "servingSizeUnit": usda_data.get("servingSizeUnit"),
        "foodNutrients": usda_data.get("foodNutrients", []),
        "foodPortions": usda_data.get("foodPortions", [])
    }
    
    # Keep only essential nutrients to reduce size further
    essential_nutrients = [
        "Energy", "Protein", "Carbohydrate", "Total lipid (fat)", 
        "Fiber", "Sugars", "Sodium", "Calcium", "Iron"
    ]
    
    if filtered["foodNutrients"]:
        filtered["foodNutrients"] = [
            nutrient for nutrient in filtered["foodNutrients"]
            if any(essential in nutrient.get("nutrient", {}).get("name", "") 
                  for essential in essential_nutrients)
        ]
    
    return filtered
