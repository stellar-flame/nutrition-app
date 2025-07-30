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
            "user_serving_size": {
                "type": "string",
                "description": "User specified serving size, e.g., '1 cup', '100g'. If not specified, assume a single serving size.",
            },
            "single_serving_size": {
                "type": "string",
                "description": "Determine a typical single serving size for the food item, e.g., '100g', '1 cup'.",
            },
            "food_description": {
                "type": "string",
                "description": "Optimize search term for USDA database. For fruits/vegetables, add 'raw' (e.g., 'apple raw')."
            }
        },
        "required": ["food_description"]
    }
}
