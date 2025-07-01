"""
OpenAI function tool definitions for the nutrition app.
"""

# USDA FoodData Central API tool definition
USDA_FUNCTION = {
    "type": "function",
    "name": "lookup_usda_nutrition",
    "description": "Search USDA FoodData Central database. Reject vague terms",
    "parameters": {
        "type": "object",
        "properties": {
            "food_description": {
                "type": "string",
                "description": "Optimize search term for USDA database. For fruits/vegetables, add 'raw' (e.g., 'apple raw')."
            }
        },
        "required": ["food_description"]
    }
}
