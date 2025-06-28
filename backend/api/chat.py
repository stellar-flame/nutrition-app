from fastapi import APIRouter, HTTPException
from openai import OpenAI
from datetime import datetime
import os
from dotenv import load_dotenv
from models import ChatRequest, ChatResponse
from client.usda_client import USDAClient
from tools_def import USDA_FUNCTION, SELECT_BEST_USDA_FUNCTION, GET_USDA_NUTRITION_FUNCTION


router = APIRouter()

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize USDA client
usda_client = USDAClient()

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

# Define USDA lookup function for OpenAI tools
async def lookup_usda_nutrition(food_description: str) -> dict:
    """Look up nutrition data from USDA FoodData Central"""
    try:
        # Get multiple search results for OpenAI to choose from
        foods = await usda_client.search_food(food_description, page_size=5)
        if foods:
            # Format the search results for OpenAI to analyze
            formatted_results = []
            for food in foods:
                formatted_results.append({
                    "description": food.get("description", ""),
                    "fdc_id": food.get("fdcId", ""),
                    "data_type": food.get("dataType", "")
                })
            
            return {
                "success": True,
                "search_results": formatted_results,
                "count": len(formatted_results)
            }
        return {"success": False, "error": "No USDA data found"}
    except Exception as e:
        return {"success": False, "error": str(e)}

async def select_best_usda_match(user_description: str, search_results: list) -> dict:
    """Select the best matching food from USDA search results"""
    try:
        if not search_results:
            return {"success": False, "error": "No search results provided"}
        
        # OpenAI will decide which result to pick or reject all
        # For now, return first result - OpenAI logic will override this
        best_match = search_results[0]
        print(best_match)  # Debugging: print the selected match
        return {
            "success": True,
            "selected_fdc_id": best_match.get("fdc_id"),
            "selected_description": best_match.get("description"),
            "user_description": user_description,
            "available_options": len(search_results)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

async def get_usda_nutrition_details(user_description: str, fdc_id: str) -> dict:
    """Fetch detailed nutrition data from USDA and format it"""
    try:
        detailed_food = await usda_client.get_food_details(fdc_id)
        if not detailed_food:
            return {"success": False, "error": "Could not fetch food details"}
        
        filtered_food = filter_usda_json(detailed_food)

        return {
            "success": True,
            "nutrition_data": filtered_food,
            "food_description": detailed_food.get('description')
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# Define the instructions for the Responses API
ASSISTANT_INSTRUCTIONS = (
    "You are a nutrition assistant. When the user describes a meal:\n\n"
    "VALIDATION: First check if the user's description is specific enough. If it's too vague (like 'chicken', 'bread', 'fruit', 'cereal'), ask for more details instead of searching. However accept terms like 'apple' or other instances of fruit or vegetable.\n\n"
    "If specific enough:\n"
    "1. Use lookup_usda_nutrition to search for the food\n"
    "2. Use select_best_usda_match to pick the best option (or reject all if none match well)\n"
    "3. If result is not none, use get_usda_nutrition_details to get detailed nutrition data.\n"
    "4. Format the final response as JSON\n\n"
    "Always respond using JSON with these fields:\n\n"
    "{\n"
    '  "intent": "log_food",\n'
    '  "description": string,\n'
    '  "calories": number,\n'
    '  "protein": number,\n'
    '  "fiber": number,\n'
    '  "carbs": number,\n'
    '  "fat": number,\n'
    '  "sugar": number,\n'
    '  "assumptions": string (mention if data is from USDA or estimated)\n'
    "}\n\n"
    "If description is too vague, USDA lookup fails, or no good matches found, respond with:\n"
    "{\n"
    ' "intent": "chat",\n'
    ' "response": "...(ask for clarification)"\n'
    "}\n\n"
    "Respond with only the JSON block, no extra commentary."
)


# Register function implementations for Responses API
async def execute_function_call(function_name: str, arguments: dict):
    """Execute function calls for the Responses API"""
    if function_name == "lookup_usda_nutrition":
        print(f"Executing USDA lookup for: {arguments.get('food_description', '')}")
        return await lookup_usda_nutrition(arguments.get("food_description", ""))
    elif function_name == "select_best_usda_match":
        print(f"Selecting best match for: {arguments.get('user_description', '')}")
        selected_fdc_id = arguments.get("selected_fdc_id", "")
        
        if selected_fdc_id == "none":
            return {
                "success": False, 
                "error": "No suitable matches found",
                "should_ask_clarification": True
            }
        
        return await select_best_usda_match(
            arguments.get("user_description", ""),
            arguments.get("search_results", [])
        )
    elif function_name == "get_usda_nutrition_details":
        print(f"Getting nutrition details for FDC ID: {arguments.get('fdc_id', '')}")
        return await get_usda_nutrition_details(
            arguments.get("user_description", ""),
            arguments.get("fdc_id", "")
        )
    return {"success": False, "error": f"Unknown function: {function_name}"}


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
    
    # Create response using Responses API with function calling
    response_params = {
        "model": "gpt-4o-mini",
        "input": input_messages,
        "instructions": ASSISTANT_INSTRUCTIONS,
        "tools": [USDA_FUNCTION, SELECT_BEST_USDA_FUNCTION, GET_USDA_NUTRITION_FUNCTION],
        "tool_choice": "auto"
    }
    
    # Add previous_response_id if continuing conversation
    if request.conversation_id:
        response_params["previous_response_id"] = request.conversation_id
    
    response = client.responses.create(**response_params)

    # Process the structured response - let OpenAI handle tool chaining
    if response.output and len(response.output) > 0:
        try:
            # 2. Loop over tool calls
            while response.output and response.output[0].type == "function_call":
                call = response.output[0]
                import json
                args = json.loads(call.arguments)

                # 3. Run the actual function locally
                result = await execute_function_call(call.name, args)

                # 4. Submit tool output back to OpenAI
                response_params = {
                    "model": "gpt-4o-mini",
                    "input": [{"role": "system", "content": json.dumps(result)}],
                    "instructions": ASSISTANT_INSTRUCTIONS,
                    "tools": [USDA_FUNCTION, SELECT_BEST_USDA_FUNCTION, GET_USDA_NUTRITION_FUNCTION],
                    "tool_choice": "auto"
                }
            
                response = client.responses.create(**response_params)        # Handle regular text response 
            
            call = response.output[0]            
            if hasattr(call, 'content') and call.content and len(call.content) > 0:
                response_text = call.content[0].text
                
                # Clean up markdown code blocks if present
                import re
                clean_text = response_text.strip()
                clean_text = re.sub(r'^```json\s*', '', clean_text)
                clean_text = re.sub(r'^```\s*', '', clean_text)
                clean_text = re.sub(r'\s*```$', '', clean_text)
                clean_text = clean_text.strip()
                
                # Parse the JSON from the response
                import json
                meal_data = json.loads(clean_text)
                
                if meal_data.get("intent") == "log_food":
                    nutrition_estimate = {
                        "id": None,
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




