from fastapi import APIRouter, HTTPException
from openai import OpenAI
from datetime import datetime
import os
from dotenv import load_dotenv
from models import ChatRequest, ChatResponse
from client.usda_client import USDAClient


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

# OpenAI function definition
USDA_FUNCTION = {
    "type": "function",
    "name": "lookup_usda_nutrition",
    "description": "Search USDA FoodData Central database and return multiple food options for you to choose the best match",
    "parameters": {
        "type": "object",
        "properties": {
            "food_description": {
                "type": "string",
                "description": "Optimized search term for USDA database. For fruits/vegetables, add 'raw' (e.g., 'apple raw'). For cooked foods, specify cooking method (e.g., 'chicken grilled'). Focus on the main food item."
            }
        },
        "required": ["food_description"]
    }
}
# Define the instructions for the Responses API
ASSISTANT_INSTRUCTIONS = (
    "You are a nutrition assistant. When the user describes a meal:\n\n"
    "1. FIRST: Try to look up the food in the USDA database using the lookup_usda_nutrition function\n"
    "2. If USDA data is found, use it and respond with intent: 'log_food'\n" 
    "3. If USDA lookup fails or returns no data, estimate the nutrition yourself\n\n"
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
    "If you cannot estimate nutrition values, respond with:\n"
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
        print (f"Executing USDA lookup for: {arguments.get('food_description', '')}")
        return await lookup_usda_nutrition(arguments.get("food_description", ""))
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
        "tools": [USDA_FUNCTION],
        "tool_choice": "auto"
    }
    
    # Add previous_response_id if continuing conversation
    if request.conversation_id:
        response_params["previous_response_id"] = request.conversation_id
    
    response = client.responses.create(**response_params)

    # Process the structured response
    if response.output and len(response.output) > 0:
        try:
            # Get the message from the response
            message = response.output[0]
            response_text = None
            
            # Check if this is a function tool call
            if hasattr(message, 'type') and message.type == 'function_call':
                # Function was called - execute it manually
                if message.name == "lookup_usda_nutrition":
                    import json
                    args = json.loads(message.arguments)
                    print(f"🔍 Executing USDA lookup for: {args.get('food_description', '')}")
                    usda_result = await lookup_usda_nutrition(args["food_description"])
                    print(f"USDA lookup result: {usda_result}")
                    # Create a follow-up prompt with USDA data
                    if usda_result.get("success"):
                        search_results = usda_result["search_results"]
                        results_text = ""
                        for i, result in enumerate(search_results, 1):
                            results_text += f"{i}. {result['description']} (FDC ID: {result['fdc_id']})\n"
                        
                        follow_up_prompt = f"""
User described: {request.description}

USDA database search found {usda_result['count']} options:
{results_text}

Instructions:
1. Pick the BEST matching food option from the list above that matches what the user described
2. I will provide you with the detailed nutrition data for your chosen option
3. Respond with ONLY the FDC ID number of your chosen option

Choose the FDC ID:"""
                    else:
                        follow_up_prompt = f"User described: {request.description}\n\nUSDA lookup failed: {usda_result.get('error')}. Please estimate the nutrition values yourself and respond with JSON format."
                    
                    # Make a first call to let OpenAI pick the best option
                    print(f"📤 Making selection call...")
                    selection_response = client.responses.create(
                        model="gpt-4o",
                        input=[{"role": "user", "content": follow_up_prompt}],
                        instructions="You are helping select the best food match. Respond with ONLY the FDC ID number."
                    )
                    
                    if selection_response.output and len(selection_response.output) > 0:
                        selection_message = selection_response.output[0]
                        if hasattr(selection_message, 'content') and selection_message.content and len(selection_message.content) > 0:
                            selected_fdc_id = selection_message.content[0].text.strip()
                            print(f"🎯 OpenAI selected FDC ID: {selected_fdc_id}")
                            
                            # Get detailed nutrition data for selected food
                            detailed_food = await usda_client.get_food_details(selected_fdc_id)
                            if detailed_food:
                                # Filter USDA JSON to reduce token usage
                                filtered_food = filter_usda_json(detailed_food)
                                final_prompt = f"""
User described: {request.description}

You selected: {detailed_food.get('description')}

Here is the filtered USDA FoodData Central JSON data:
{json.dumps(filtered_food, indent=2)}

Instructions:
1. Extract the nutrition data from this USDA JSON
2. Look in the "foodNutrients" array for nutrients like Energy, Protein, Carbohydrate, Total lipid (fat), Fiber, Sugars
3. Convert to the required JSON format for intent: "log_food"
4. Mention "Data from USDA FoodData Central" in assumptions

Respond with JSON format only.
"""
                                
                                # Make final call to format the JSON response
                                print(f"📤 Making final formatting call...")
                                final_response = client.responses.create(
                                    model="gpt-4o-mini",
                                    input=[{"role": "user", "content": final_prompt}],
                                    instructions=ASSISTANT_INSTRUCTIONS
                                )
                                
                                if final_response.output and len(final_response.output) > 0:
                                    final_message = final_response.output[0]
                                    if hasattr(final_message, 'content') and final_message.content and len(final_message.content) > 0:
                                        response_text = final_message.content[0].text
                                        print(f"✅ Got final response text: {response_text[:100]}...")
                                    else:
                                        print("❌ No content in final response")
                                else:
                                    print("❌ No output in final response")
                            else:
                                print("❌ Could not get detailed food data")
                        else:
                            print("❌ No selection content")
                    else:
                        print("❌ No selection output")
            elif hasattr(message, 'content') and message.content and len(message.content) > 0:
                # Regular text response
                response_text = message.content[0].text
            
            if response_text:
                # Clean up markdown code blocks if present
                import re
                clean_text = response_text.strip()
                # Remove markdown json code blocks
                clean_text = re.sub(r'^```json\s*', '', clean_text)
                clean_text = re.sub(r'^```\s*', '', clean_text)
                clean_text = re.sub(r'\s*```$', '', clean_text)
                clean_text = clean_text.strip()
                
                print(f"🧹 Cleaned response text: {clean_text[:100]}...")
                
                # Parse the JSON from the response
                import json
                meal_data = json.loads(clean_text)
                
                if meal_data.get("intent") == "log_food":
                    # Create nutrition estimate
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




