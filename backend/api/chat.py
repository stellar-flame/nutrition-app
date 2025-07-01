from fastapi import APIRouter
from openai import OpenAI
from datetime import datetime
import os
import json
from dotenv import load_dotenv
from models import ChatRequest, ChatResponse, StepResponse
from client.usda_client import USDAClient
from llm.tools import USDA_FUNCTION
from llm.helpers import (
    create_openai_response, 
    create_error_response, 
    extract_response_text, 
    clean_json_text, 
    filter_usda_json
)


router = APIRouter()

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

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


async def prompt_for_food_lookup(client: OpenAI, description: str, prev_response_id: str) -> StepResponse:
    """STEP 1: Validation and USDA Search (gpt-4o-mini)"""
    instructions = (
        "You are a nutrition assistant. Validate the user's food description:\n\n"
        "This may be part of a conversation where the user describes a food they ate.\n"
        "You should infer what they are saying from previous history:\n\n"
        "1. Try and infer what the user means if they provide a vague description.\n"
        "2. If specific enough (like 'grilled chicken breast', 'apple'), search USDA database\n\n"
        "3. If too vague and cooking method matters (like 'chicken', 'bread', 'fruit', 'vegetable'), respond with intent: 'chat' asking for specifics\n"
        "4. Assume a single portion size unless specified otherwise.\n\n"
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
            print(f"USDA lookup failed: {usda_result.get('error', 'Unknown error')}")
            return StepResponse(
                success=False,
                response_id=response.id,
                error_message="I couldn't find that food in the USDA database. Could you be more specific?"
            )
        

        print(f"SUCESS Call id: {call.call_id}")
        return StepResponse(
            success=True,
            response_id=response.id,
            tool_call_id=call.call_id,
            data={
                "search_results": usda_result["search_results"],
                "count": usda_result["count"]
            }
        )
    else:
        # Handle validation failure or chat response from step 1
        if response.output and response.output[0].content:
            return StepResponse(
                success=False,
                response_id=response.id,
                error_message=extract_response_text(response)
            )
    
async def prompt_for_food_selection(client: OpenAI, description: str, step1_result: StepResponse) -> StepResponse:
    """STEP 2: Food Selection (gpt-4o)"""
    if not step1_result.success or not step1_result.data or not step1_result.data.get("search_results"):
        return StepResponse(
            success=False,
            response_id=step1_result.response_id,
            error_message="No search results available for selection"
        )
    
    search_results = step1_result.data["search_results"]
    results_text = ""
    for i, result in enumerate(search_results, 1):
        results_text += f"{i}. {result['description']} (FDC ID: {result['fdc_id']})\n"
    
    input_content = [{"role": "system", "content": f"User requested nutritional for: {description}\n"}]
    input_content.append({                             
        "type": "function_call_output",
        "call_id": step1_result.tool_call_id,
        "output": f"USDA options:\n{results_text}"
    })

    print(f"Call id: {step1_result.tool_call_id}")

    instructions = (
        "Select the BEST matching food from these USDA search results. "
        "Try to match the user's description as closely as possible\n\n"
        "If NONE match well, respond with 'none'. "
        "Otherwise, respond with ONLY the FDC ID of the best match."
    )

    response = await create_openai_response(
        client, "gpt-4o", input_content, instructions, 
        step1_result.response_id
    )
    
    selected_fdc_id = extract_response_text(response)

    if selected_fdc_id == "none":
        return StepResponse(
            success=False,
            response_id=response.id,
            error_message="None of the USDA results match your description well. Could you be more specific?"
        )
    else:
        return StepResponse(
            success=True,
            response_id=response.id,
            data={"selected_fdc_id": selected_fdc_id}
        )


async def prompt_for_usda_nutrition_details(client: OpenAI, description: str, step2_result: StepResponse) -> StepResponse:
    """STEP 3a: Nutrition Extraction (gpt-4o-mini)"""
    if not step2_result.success or not step2_result.data or not step2_result.data.get("selected_fdc_id"):
        return StepResponse(
            success=False,
            response_id=step2_result.response_id,
            error_message="No selected food ID available for nutrition extraction"
        )
    
    fdc_id = step2_result.data["selected_fdc_id"]
    nutrition_result = await get_usda_nutrition_details(description, fdc_id)
    
    if not nutrition_result.get("success"):
        return StepResponse(
            success=False,
            response_id=step2_result.response_id,
            error_message="I had trouble getting nutrition details. Please try again."
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
        instructions, step2_result.response_id
    )
    
    return StepResponse(
        success=True,
        response_id=response.id,
        data={"response_text": extract_response_text(response)}
    )


async def prompt_for_llm_estimate(client: OpenAI, description: str, prev_response: StepResponse) -> StepResponse:
    """STEP 3b: Nutrition Extraction (gpt-4o-mini)"""
    instructions = (
        "You are a nutrition assistant. "
        "Estimate the nutrition data for the food described by the user.\n\n"
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
        '  "assumptions": string any assumptions made and mention "Estimate provided by LLM" \n'
        "}\n\n"
        "If you cannot estimate, respond with intent: 'chat' and ask for more details.\n"
    )

    response = await create_openai_response(
        client, "gpt-4o-mini",
        [{"role": "user", "content": description}],
        instructions, prev_response.response_id
    )
    
    return StepResponse(
        success=True,
        response_id=response.id,
        data={"response_text": extract_response_text(response)}
    )

@router.post("/openai/chat", response_model=ChatResponse)
async def openai_chat(request: ChatRequest):
    client = OpenAI(api_key=OPENAI_API_KEY)
    current_conversation_id = request.conversation_id

    # STEP 1: Food Validation and USDA Search (gpt-4o-mini)
    step1_result = await prompt_for_food_lookup(client, request.description, current_conversation_id)
    if not step1_result.success:
        return ChatResponse(
            message=step1_result.error_message,
            conversation_id=step1_result.response_id
        )
    
    # STEP 2: Food Selection (gpt-4o)
    step2_result = await prompt_for_food_selection(client, request.description, step1_result)
    if not step2_result.success:
        return ChatResponse(
            message=step2_result.error_message,
            conversation_id=step2_result.response_id
        )
    
    # STEP 3: Nutrition Extraction (gpt-4o-mini)
    step3_result = await prompt_for_usda_nutrition_details(client, request.description, step2_result)
    if not step3_result.success:
        step3_result = await prompt_for_llm_estimate(client, request.description, step2_result)
        if not step3_result.success:    
            return ChatResponse(
                message=step3_result.error_message,
                conversation_id=step3_result.response_id
            )
    
    response_text = step3_result.data["response_text"]
    
    if not response_text or "intent" not in response_text:
        return ChatResponse(
            message="I had trouble processing that. Could you please try again?",
            conversation_id=step3_result.response_id
        )
    
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
            conversation_id=step3_result.response_id,
        )
    else:
        return ChatResponse(
            message=meal_data.get("response", "I had trouble processing that."),
            conversation_id=step3_result.response_id
        )




