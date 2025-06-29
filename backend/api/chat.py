from fastapi import APIRouter, HTTPException
from openai import OpenAI
from datetime import datetime
import os
import json
from dotenv import load_dotenv
from models import ChatRequest, ChatResponse
from client.usda_client import USDAClient
from tools_def import USDA_FUNCTION, SELECT_BEST_USDA_FUNCTION, GET_USDA_NUTRITION_FUNCTION


router = APIRouter()

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize USDA client
usda_client = USDAClient()

# Helper functions to reduce code duplication
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
    import re
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


async def prompt_for_food_lookup(client: OpenAI, description: str, prev_response_id: str) -> dict | ChatResponse:
    """STEP 1: Validation and USDA Search (gpt-4o-mini)"""
    instructions = (
        "You are a nutrition assistant. Validate the user's food description:\n\n"
        "1. If too vague (like 'chicken', 'bread', 'fruit'), respond with intent: 'chat' asking for specifics\n"
        "2. If specific enough (like 'grilled chicken breast', 'apple'), search USDA database\n\n"
        "Use the lookup_usda_nutrition function to search, then respond with:\n"
        "- If search successful: Return the search results as JSON\n"
        "- If too vague or search fails: Respond with intent: 'chat'"
    )
    
    response = await create_openai_response(
        client, "gpt-4o-mini", 
        [{"role": "user", "content": description}],
        instructions, prev_response_id, [USDA_FUNCTION]
    )
    
    # Execute USDA search if tool was called
    if response.output and response.output[0].type == "function_call":
        call = response.output[0]
        args = json.loads(call.arguments)
        usda_result = await lookup_usda_nutrition(args.get("food_description", ""))
        
        if not usda_result.get("success"):
            return create_error_response(
                "I couldn't find that food in the USDA database. Could you be more specific?",
                prev_response_id
            )
        
        usda_result["tool_call"] = call.call_id
        usda_result["response_id"] = response.id
        return usda_result
    else:
        # Handle validation failure or chat response from step 1
        if response.output and response.output[0].content:
            return create_error_response(
                extract_response_text(response),
                prev_response_id
            )
    
async def prompt_for_food_selection(client: OpenAI, description: str, search_results: dict) -> dict | ChatResponse:
    """STEP 2: Food Selection (gpt-4o)"""
    print(search_results)  # Debugging line to inspect search results
    if search_results.get("search_results"):
        results_text = ""
        for i, result in enumerate(search_results["search_results"], 1):
            results_text += f"{i}. {result['description']} (FDC ID: {result['fdc_id']})\n"
        
        tool_call_id = search_results["tool_call"]
        input_content = [{"role": "system", "content": f"User requested nutritional for: {description}\n"}]
        input_content.append({                             
            "type": "function_call_output",
            "call_id": tool_call_id,
            "output": f"USDA options:\n{results_text}"
        })

        instructions = (
            "Select the BEST matching food from these USDA search results. "
            "If NONE match well, respond with 'none'. "
            "Otherwise, respond with ONLY the FDC ID of the best match."
        )
        
        prev_response_id = search_results.get("response_id")

        response = await create_openai_response(
            client, "gpt-4o", input_content, instructions, 
            prev_response_id, [USDA_FUNCTION]
        )
        
        selected_fdc_id = extract_response_text(response)
    
        if selected_fdc_id == "none":
            return create_error_response(
                "None of the USDA results match your description well. Could you be more specific?",
                prev_response_id
            )
        else:
            return {"selected_fdc_id": selected_fdc_id, "response_id": response.id}


async def prompt_for_usda_nutrition_details(client: OpenAI, description: str, selected_food: dict) -> dict:
    """STEP 3: Nutrition Extraction (gpt-4o-mini)"""
    fdc_id = selected_food.get("selected_fdc_id")
    prev_response_id = selected_food.get("response_id")
    nutrition_result = await get_usda_nutrition_details(description, fdc_id)
    
    if not nutrition_result.get("success"):
        return create_error_response(
            "I had trouble getting nutrition details. Please try again.",
            prev_response_id
        )
    
    nutrition_data = filter_usda_json(nutrition_result["nutrition_data"])
    instructions = (
        "Extract nutrition data from this USDA JSON and format as the required JSON response. "
        "Look for Energy, Protein, Carbohydrate, Total lipid (fat), Fiber, Sugars. "
        "Final response should include:\n\n"
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
        "Respond with intent: 'log_food' and mention 'Data from USDA FoodData Central' in assumptions."
    )
    
    input_content = f"User described: {description}\n\nUSDA JSON:\n{json.dumps(nutrition_data, indent=2)}"
    
    response = await create_openai_response(
        client, "gpt-4o-mini",
        [{"role": "user", "content": input_content}],
        instructions, prev_response_id
    )
    
    return {
        "response_text": extract_response_text(response), 
        "response_id": response.id
    }

@router.post("/openai/chat", response_model=ChatResponse)
async def openai_chat(request: ChatRequest):
    client = OpenAI(api_key=OPENAI_API_KEY)
    current_conversation_id = request.conversation_id

    # STEP 1: Food Validation and USDA Search (gpt-4o-mini)
    lookup_result = await prompt_for_food_lookup(client, request.description, current_conversation_id)
    if (lookup_result is ChatResponse):
        return lookup_result
    
    # STEP 2: Food Selection (gpt-4o)
    food_selection = await prompt_for_food_selection(client, request.description, lookup_result)
    if isinstance(food_selection, ChatResponse):
        return food_selection
    
    # STEP 3: Nutrition Extraction (gpt-4o-mini)
    response = await prompt_for_usda_nutrition_details(client, request.description, food_selection)
    response_text = response.get("response_text")
    prev_response_id = response.get("response_id")
    
    # Clean up markdown code blocks
    clean_text = clean_json_text(response_text)
    
    # Parse JSON and return nutrition estimate
    meal_data = json.loads(clean_text)
    
    print(f"Parsed meal data: {meal_data}")
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
            conversation_id=prev_response_id,
        )
    else:
        return ChatResponse(
            message=meal_data.get("response", "I had trouble processing that."),
            conversation_id=prev_response_id
        )




