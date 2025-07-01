"""
OpenAI helper functions and utilities for the nutrition app.
"""
from typing import Union
from openai import OpenAI
from models import ChatResponse
import re
import json


async def create_openai_response(client: OpenAI, model: str, input_content, instructions: str, 
                                prev_response_id: str = None, tools: list = None) -> object:
    """Standardized OpenAI response creation"""
    params = {
        "model": model,
        "input": input_content,
        "instructions": instructions
    }
    
    if prev_response_id:
        params["previous_response_id"] = prev_response_id
    if tools:
        params["tools"] = tools
        params["tool_choice"] = "auto"
    
    return client.responses.create(**params)


def create_error_response(message: str, conversation_id: str) -> ChatResponse:
    """Standardized error response creation"""
    return ChatResponse(
        message=message,
        conversation_id=conversation_id
    )


def extract_response_text(response) -> str:
    """Extract and clean text from OpenAI response"""
    if response.output and response.output[0].content:
        return response.output[0].content[0].text.strip()
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
