from dotenv import load_dotenv
import os
import json
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# --- Define the function schema for OpenAI ---
nutrition_function = {
    "name": "extract_nutrition",
    "description": "Estimate nutrition data from a food description. Always include numerical values for all nutritional fields.",
    "parameters": {
        "type": "object",
        "properties": {
            "calories": {
                "type": "number",
                "description": "Estimated calories in the food item"
            },
            "protein": {
                "type": "number", 
                "description": "Protein content in grams"
            },
            "fiber": {
                "type": "number",
                "description": "Dietary fiber in grams"
            }, 
            "carbs": {
                "type": "number",
                "description": "Total carbohydrates in grams"
            },
            "fat": {
                "type": "number",
                "description": "Total fat content in grams"
            },
            "sugar": {
                "type": "number",
                "description": "Sugar content in grams"
            },
            "description": {
                "type": "string",
                "description": "Normalized food description"
            },
            "assumptions": {
                "type": "string",
                "description": "Any assumptions made about portion size, brand, or preparation method"
            },
        },
        "required": ["calories", "protein", "fiber", "carbs", "fat", "sugar", "description"]
    }
}

# Create the chat model
chat = ChatOpenAI(
    model_name='gpt-4',
    temperature=0,
    max_tokens=150,
    openai_api_key=OPENAI_API_KEY,
    request_timeout=30,
    model_kwargs={"tools": [{"type": "function", "function": nutrition_function}]},
    streaming=False
)

# Define our messages
messages = [
    SystemMessage(content=(
        "You are a nutritional assistant. Use the extract_nutrition function when estimating values. "
        "Always provide numeric values for calories, protein, carbs, fat, sugar, and fiber. "
        "Make reasonable estimations based on standard portions when specifics aren't provided. "
        "ALWAYS USE THE extract_nutrition FUNCTION to process food descriptions."
    )),
    HumanMessage(content="banana")
]

# Call the OpenAI API
print("Calling OpenAI API...")
response = chat.invoke(messages)

# Extract tool calls if present
tool_calls = getattr(response, "tool_calls", [])
print(f"Tool calls: {tool_calls}")

if tool_calls:
    # Try to process the tool calls
    if hasattr(tool_calls[0], "function") and hasattr(tool_calls[0].function, "arguments"):
        args = tool_calls[0].function.arguments
        print(f"Function arguments (object): {args}")
    elif isinstance(tool_calls[0], dict):
        if "function" in tool_calls[0]:
            args = tool_calls[0]["function"]["arguments"]
            print(f"Function arguments (dict.function): {args}")
        elif "args" in tool_calls[0]:
            args = tool_calls[0]["args"]
            print(f"Function arguments (dict.args): {args}")
        else:
            args = tool_calls[0]
            print(f"Function arguments (dict): {args}")
    else:
        print(f"Unknown tool_calls structure: {type(tool_calls[0])} - {tool_calls[0]}")
