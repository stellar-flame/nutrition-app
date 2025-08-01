from fastapi import APIRouter, HTTPException
from openai import OpenAI
from datetime import datetime
import json
from dotenv import load_dotenv
from database.schemas import ChatRequest, ChatResponse, FoodItem, FoodItemList
from client.usda_client import USDAClient
from llm.tools import USDA_FUNCTION
from llm.helpers import (
    create_openai_response, 
    extract_response_text, 
    clean_json_text, 
    filter_usda_json
)
from llm.prompts import (
    FOOD_LOOKUP_PROMPT,
    INTENT_CLASSIFICATION_PROMPT,
    SELECTION_PROMPT,
    USDA_EXTRACTION_PROMPT,
    LLM_ESTIMATION_PROMPT,
    CHAT_RESPONSE_PROMPT
)
from utils.secrets import get_secret


router = APIRouter()

# Initialize USDA client
usda_client = USDAClient()

# Define USDA lookup function for OpenAI tools
async def lookup_usda_nutrition(food_description: str) -> dict:
    """Look up nutrition data from USDA FoodData Central"""
    try:
        # Get multiple search results for OpenAI to choose from
        foods = await usda_client.search_food(food_description, page_size=20)
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
        return {"success": False, 
                "error": f"No USDA data found for {food_description}"}
    except Exception as e:
        return {"success": False, 
                "error": str(e)}


async def get_usda_nutrition_details(fdc_id: str) -> dict:
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



async def food_lookup(client: OpenAI, request: ChatRequest) -> ChatResponse:
    chat_prompt = build_chat_prompt(request, FOOD_LOOKUP_PROMPT)

    response = client.responses.parse(
        model="gpt-4o-mini",
        input=[{"role": "user", "content": chat_prompt}],
        temperature=0.3,
        text_format=FoodItemList,
    )

    food_items = response.output_parsed.items if response.output_parsed else []

    if not food_items:
        return ChatResponse(
            conversation_id=response.id,
            message="No food items found in the description. Please provide a more detailed description."
        )

    meal_results = []
    errors = []
    for item in food_items:
        usda_result = await lookup_usda_nutrition(item.description)
        nutritional_estimate = None
        if (usda_result.get("success")):
            results_text = f"Result for Food Item: {item.description}:\n"
            for i, result in enumerate(usda_result.get("search_results", []), 1):
                results_text += f"{i}. {result['description']} (FDC ID: {result['fdc_id']})\n"
            
            response = await create_openai_response(
                client,
                "gpt-4o-mini",
                [{"role": "user", "content": f"User requested nutritional for: {item.description}, USDA returned {results_text}\n"}],
                SELECTION_PROMPT,
                response.id
            )
            response_text = extract_response_text(response)
            clean_text = clean_json_text(response_text)
            selected_item = json.loads(clean_text)
            fdc_id = selected_item.get("id", "none") if not isinstance(selected_item, list) else selected_item[0].get("id", "none") 
            nutrition_result = await get_usda_nutrition_details(fdc_id)

            if nutrition_result.get("success"):
                nutrition_data = filter_usda_json(nutrition_result["nutrition_data"])
                input_content = (
                    "USDA returned nutritional estimate for: \n"
                    f"{fdc_id}\n\nUSDA JSON:\n{json.dumps(nutrition_data, indent=2)}"
                )
                response = await create_openai_response(
                    client, "gpt-4o-mini",
                    [{"role": "user", "content": input_content}],
                    USDA_EXTRACTION_PROMPT, response.id
                )
                response_text = extract_response_text(response)
                clean_text = clean_json_text(response_text)
                nutritional_estimate = extract_nutrition_estimate(clean_text, item)

        if nutritional_estimate is None:
            item_lookup = f"Lookup nutrition for {item.user_serving_size}g {item.description}"
            print(f"LLM Processing for {item_lookup}")
            response = await create_openai_response(
                client, "gpt-4o-mini",
                [{"role": "user", "content": item_lookup}],
                LLM_ESTIMATION_PROMPT, response.id
            )
            response_text = extract_response_text(response)
            nutritional_estimate = extract_nutrition_estimate(response_text, item)

        if nutritional_estimate is not None:
            meal_results.append(nutritional_estimate)
        else:
            errors.append(f"Could not estimate nutrition for {item.description}")

    return ChatResponse(
        conversation_id=response.id,
        message="Nutrition lookup completed",
        meals=meal_results,
        errors=errors
    )

def extract_nutrition_estimate(response_text: str, item: FoodItem) -> dict | None:
    # # Clean up markdown code blocks
    clean_text = clean_json_text(response_text)
    
    # # Parse JSON and return nutrition estimate
    meal_data = json.loads(clean_text)
    
    serving_size = item.user_serving_size or item.single_serving_size

    if meal_data.get("intent") == "log_food":
        nutrition_estimate = {
            "id": None,
            "timestamp": datetime.now().isoformat(),
            "calories": get_value_per_serving_size(meal_data.get("calories", 0), serving_size),
            "protein": get_value_per_serving_size(meal_data.get("protein", 0), serving_size),
            "fiber": get_value_per_serving_size(meal_data.get("fiber", 0), serving_size),
            "carbs": get_value_per_serving_size(meal_data.get("carbs", 0), serving_size),
            "fat": get_value_per_serving_size(meal_data.get("fat", 0), serving_size),
            "sugar": get_value_per_serving_size(meal_data.get("sugar", 0), serving_size),
            "quantity": f"{serving_size}g",
            "description": meal_data.get("description", item.description),
            "assumptions": meal_data.get("assumptions", None)
        }
        return nutrition_estimate
    else:
        return None

def get_value_per_serving_size(value: int, user_serving_size: int) -> int:
    if value is None:
        return 0.0
    return round(value / 100 * user_serving_size,2)

def build_chat_prompt(request: ChatRequest, prompt: str) -> str:
    """Build chat prompt from request history and description"""
    
    # Format conversation history
    history_text = ""
    if request.history:
        for msg in request.history:
            if msg["role"] == "user":
                history_text += f"User: {msg['content']}\n"
            elif msg["role"] == "assistant":
                history_text += f"Assistant: {msg['content']}\n"
    
    # Build the chat prompt
    chat_prompt = prompt.format(
        history=history_text if history_text else "No previous conversation.",
        message=request.description
    )
    
    return chat_prompt


async def chat_action(client: OpenAI, request: ChatRequest) -> ChatResponse:
    # Generate a proper chat response using conversation history
    chat_prompt = build_chat_prompt(request, CHAT_RESPONSE_PROMPT)

    # Generate chat response using LLM
    try:      
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": chat_prompt}],
            temperature=0.3,
            max_tokens=500
        )

        generated_message = response.choices[0].message.content.strip()

        return ChatResponse(
            conversation_id=response.id,
            message=generated_message
        )
        
    except Exception as e:
        print(f"Error generating chat response: {e}")
        return ChatResponse(
            conversation_id=response.id,
            message="I apologize, but I'm having trouble generating a response right now. Please try again."
            )

@router.post("/openai/chat", response_model=ChatResponse)
async def openai_chat(request: ChatRequest):
    openai_api_key = get_secret('openai_api_key')
    if not openai_api_key:
        raise HTTPException(status_code=500, detail="OpenAI API key not available")
    
    client = OpenAI(api_key=openai_api_key)

    input_content = (
        "User says or asks the following: \n"
        f"{request.description}\n\n"
        "Conversation history: \n"
        f"{json.dumps(request.history, indent=2)}\n\n"
    )

    response = await create_openai_response(
        client,
        "gpt-4o",
        [{"role": "user", "content": input_content}],
        INTENT_CLASSIFICATION_PROMPT,
    )

    response_text = extract_response_text(response)
    response_text = clean_json_text(response_text)  
    action_data = json.loads(response_text)
    action = action_data.get("action")
    
    request.history = request.history or []
    request.history.append({
        "role": "assistant",
        "content": response_text,
        "timestamp": datetime.now().isoformat()
    })

    chat_response = None

    if action == "food_lookup":
        chat_response = await food_lookup(client, request)
    elif action == "chat":
        chat_response = await chat_action(client, request)

        
    # Append assistant response to conversation context
    if action == "food_lookup" and chat_response.meals:
        # Format food lookup response for context
        meal_summary = []
        for meal in chat_response.meals:
            meal_summary.append(f"{meal.get('description')} ({meal})")

        assistant_content = f"Meals assistant found to log: {', '.join(meal_summary)}"
        if chat_response.message:
            assistant_content += f" - {chat_response.message}"

    else:
        # Chat response
        assistant_content = chat_response.message if chat_response.message else "No response provided"
    
  
    chat_response.history.append({
        "role": "user",
        "content": request.description,
        "timestamp": datetime.now().isoformat()
    })  
    chat_response.history.append({
        "role": "assistant",
        "content": assistant_content,
        "timestamp": datetime.now().isoformat()
    })
    return chat_response


