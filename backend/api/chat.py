from fastapi import APIRouter, HTTPException
from openai import OpenAI
from datetime import datetime
import os
import json
from dotenv import load_dotenv
from database.schemas import ChatRequest, ChatResponse, StepResponse
from client.usda_client import USDAClient
from llm.tools import USDA_FUNCTION
from llm.helpers import (
    create_openai_response, 
    extract_response_text, 
    clean_json_text, 
    filter_usda_json
)
from llm.prompts import (
    LOOKUP_PROMPT,
    SELECTION_PROMPT,
    USDA_EXTRACTION_PROMPT,
    LLM_ESTIMATION_PROMPT
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
        foods = await usda_client.search_food(food_description, page_size=100)
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


async def food_lookup(client: OpenAI, description: str, prev_response_id: str) -> ChatResponse:
    response = await create_openai_response(
        client, "gpt-4o-mini", 
        [{"role": "user", "content": description}],
        LOOKUP_PROMPT, prev_response_id, [USDA_FUNCTION]
    )
    
    search_results = []      
    for output in response.output or []:
        if output.type == "function_call":
            call = output
            args = json.loads(call.arguments)
            food_description = args.get("food_description", "")
    
            usda_result = await lookup_usda_nutrition(food_description)

            # Add call_id and description to each search result
            results_text = f"Result for Food Item: {food_description}:\n"
            if (usda_result.get("success")):
                for i, result in enumerate(usda_result.get("search_results", []), 1):
                    results_text += f"{i}. {result['description']} (FDC ID: {result['fdc_id']})\n"
            else:
                results_text += f"Error: {usda_result.get('error', 'No results found')}\n"

            # Append the formatted result to search_results
            search_results.append({"output": results_text, "call_id": call.call_id, "food_description": food_description })
        else:
            if response.output and response.output[0].content:
                return ChatResponse(
                    conversation_id=response.id,
                    message=extract_response_text(response)
                )

    # If we have search results, prepare the input for the next step
    if search_results:
        input_content = [{"role": "system", "content": f"User requested nutritional for: {description}\n"}]
        # print(r.get("llm_description", "") + " : " + json.dumps(r.get("output"), indent=2))
        for r in search_results:
           input_content.append({                           
            "type": "function_call_output",
            "call_id": r.get("call_id"),
            "output": r.get("output")   
           })
        

        response = await create_openai_response(
            client, "gpt-4o", input_content, SELECTION_PROMPT, 
            response.id
        )

        response_text = extract_response_text(response)
        print(response_text)

        clean_text = clean_json_text(response_text)
        print(clean_text)

        selected_items = json.loads(clean_text)

        print (f"selected: {selected_items}")   

        meal_macros = []
        for item in selected_items:
            nutritional_estimate = None
            fdc_id = item.get("id", "none")
            if fdc_id != "none":
                print(f"Processing FDC ID: {fdc_id}")
                nutrition_result = await get_usda_nutrition_details(fdc_id)
                
                if nutrition_result.get("success"):
                    nutrition_data = filter_usda_json(nutrition_result["nutrition_data"])
                    input_content = f"USDA returned nutritional estimate for: {fdc_id}\n\nUSDA JSON:\n{json.dumps(nutrition_data, indent=2)}"
                    response = await create_openai_response(
                        client, "gpt-4o-mini",
                        [{"role": "user", "content": input_content}],
                        USDA_EXTRACTION_PROMPT, response.id
                    )

                    response_text = extract_response_text(response)
                    nutritional_estimate = extract_nutrition_estimate(response_text, description)
                    print(f"Nutritional estimate from USDA for {fdc_id}: {nutritional_estimate}")
            
            if nutritional_estimate is None:
                food_item = item.get("food_item")
                print(f"LLM Processing for {food_item}")
                response = await create_openai_response(
                    client, "gpt-4o-mini",
                    [{"role": "user", "content": food_item}],
                    LLM_ESTIMATION_PROMPT, response.id
                )
                response_text = extract_response_text(response)
                print(f"Response text for {food_item}: {response_text}")
                nutritional_estimate = extract_nutrition_estimate(response_text, food_item)
                print(f"Nutritional estimate for {food_item}: {nutritional_estimate}")
            
            if nutritional_estimate is not None:
                meal_macros.append(nutritional_estimate)
        
        print(f"Meal macros collected: {meal_macros}")
        if not meal_macros:
            return ChatResponse(
                conversation_id=response.id,
                message=f"{description} cannot be estimated. Could you please try again?"
            )
        else:
            print(f"Returning {len(meal_macros)} meal(s): {meal_macros}")
            return ChatResponse(
                conversation_id=response.id,
                meals=meal_macros
            )

def extract_nutrition_estimate(response_text: str, description: str) -> dict | None:
    # # Clean up markdown code blocks
    clean_text = clean_json_text(response_text)
    
    # # Parse JSON and return nutrition estimate
    meal_data = json.loads(clean_text)
    
    print(f"Parsed meal data: {meal_data}")
    if meal_data.get("intent") == "log_food":
        nutrition_estimate = {
            "id": None,
            "timestamp": datetime.now().isoformat(),
            "calories": meal_data.get("calories", 0),
            "protein": meal_data.get("protein", 0),
            "fiber": meal_data.get("fiber", 0),
            "carbs": meal_data.get("carbs", 0),
            "fat": meal_data.get("fat", 0),
            "sugar": meal_data.get("sugar", 0),
            "description": meal_data.get("description", description),
            "assumptions": meal_data.get("assumptions", None)
        }
        return nutrition_estimate
    else:
        return None


@router.post("/openai/chat", response_model=ChatResponse)
async def openai_chat(request: ChatRequest):
    openai_api_key = get_secret('openai_api_key')
    if not openai_api_key:
        raise HTTPException(status_code=500, detail="OpenAI API key not available")
    
    client = OpenAI(api_key=openai_api_key)
    prev_response_id = request.conversation_id

    chat_response = await food_lookup(client, request.description, prev_response_id)
    return chat_response



