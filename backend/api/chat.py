from fastapi import APIRouter, HTTPException
from openai import OpenAI

from datetime import datetime
import os
from dotenv import load_dotenv
from models import ChatRequest, ChatResponse
import json
from openai.types.beta.threads.message import Message
import re

router = APIRouter()

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# Store the assistant ID in an environment variable if it exists
ASSISTANT_ID = os.getenv("OPENAI_ASSISTANT_ID")

# Define the assistant instructions - will be used when creating a new assistant
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


def get_assistant_id():
    """
    Get or create an OpenAI assistant.
    Returns the assistant ID which can be reused in subsequent requests.
    """
    # Create a new client for each request
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    # If we already have an assistant ID, use it
    if ASSISTANT_ID:
        try:
            # Verify the assistant exists
            assistant = client.beta.assistants.retrieve(ASSISTANT_ID)
            return assistant.id
        except Exception as e:
            print(f"Error retrieving existing assistant: {e}")
            # Continue and create a new assistant
    
    # Create a new assistant
    assistant = client.beta.assistants.create(
        name="Nutrition Assistant",
        description="Helps estimate nutrition from meal descriptions.",
        model="gpt-4o",
        instructions=ASSISTANT_INSTRUCTIONS
    )
    
    # Print the assistant ID so it can be saved as an environment variable
    print(f"Created new assistant with ID: {assistant.id}")
    print("Set this ID as OPENAI_ASSISTANT_ID in your environment variables to reuse it.")
    
    return assistant.id


@router.post("/openai/chat", response_model=ChatResponse)
async def openai_chat(request: ChatRequest):
    # Create a new OpenAI client for each request
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    # Get or create assistant
    assistant_id = get_assistant_id()
    
    if request.conversation_id:
        thread = client.beta.threads.retrieve(request.conversation_id)
    else:
        thread = client.beta.threads.create()

    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=request.description,
    )

    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id=assistant_id
    )
    if run.status == "completed":
        messages = client.beta.threads.messages.list(thread_id=thread.id)
        print (f"Message {messages.data[0]}")
        
        # Handle different response structures
        try:
            meal_data = extract_json_from_message(messages.data[0])
            
            if meal_data.get("intent") == "log_food":
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
                return ChatResponse(
                    meal=nutrition_estimate,
                    conversation_id=thread.id,
                )
            elif meal_data.get("intent") == "chat": 
                return ChatResponse(
                    message=meal_data.get("response"),
                    conversation_id=thread.id,
                )
            else:
                return ChatResponse(
                    message="I didn't understand that response. Could you try again?",
                    conversation_id=thread.id
                )
        except Exception as e:
            print(f"Error processing tool call data: {e}")
            return ChatResponse(
                message="I had trouble processing the nutrition data. Could you try providing more details?",
                conversation_id=thread.id
            )
    else:   
        print(f"Run failed with status: {run.status}")
        raise HTTPException(status_code=500, detail="OpenAI run failed")        

@router.delete("/openai/thread/{conversation_id}", status_code=200)
async def delete_thread(conversation_id: str):
    try:
        # Create a new OpenAI client for each request
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        # Delete the thread using the OpenAI client
        client.beta.threads.delete(conversation_id)
        return {"status": "success", "message": "Thread deleted successfully"}
    except Exception as e:
        # Handle potential errors
        print(f"Error deleting thread {conversation_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete thread: {str(e)}")


def extract_json_from_message(message: Message) -> dict:
    # Get the raw text from the assistant's response
    text = message.content[0].text.value

    # Look for a ```json code block or fallback to entire text
    match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", text)
    json_str = match.group(1) if match else text

    # Try to parse the JSON 
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Could not parse JSON from message: {e}")


