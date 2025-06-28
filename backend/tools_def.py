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

# Tool to select the best USDA food match from search results
SELECT_BEST_USDA_FUNCTION = {
    "type": "function",
    "name": "select_best_usda_match",
    "description": "Select the best matching food from USDA search results. If NONE of the results match the user's description well, you can select 'none' to reject all results.",
    "parameters": {
        "type": "object",
        "properties": {
            "user_description": {
                "type": "string",
                "description": "The original user food description"
            },
            "search_results": {
                "type": "array",
                "description": "Array of USDA search results with fdc_id and description",
                "items": {
                    "type": "object",
                    "properties": {
                        "description": {"type": "string"},
                        "fdc_id": {"type": "string"},
                        "data_type": {"type": "string"}
                    }
                }
            },
            "selected_fdc_id": {
                "type": "string",
                "description": "The FDC ID of the selected food, or 'none' if no results match well enough"
            }
        },
        "required": ["user_description", "search_results", "selected_fdc_id"]
    }
}

# Tool to get detailed nutrition data from USDA
GET_USDA_NUTRITION_FUNCTION = {
    "type": "function", 
    "name": "get_usda_nutrition_details",
    "description": "Fetch detailed nutrition data from USDA for a specific food and format it as JSON",
    "parameters": {
        "type": "object",
        "properties": {
            "user_description": {
                "type": "string",
                "description": "The original user food description"
            },
            "fdc_id": {
                "type": "string",
                "description": "The USDA FDC ID to fetch detailed nutrition data for"
            }
        },
        "required": ["user_description", "fdc_id"]
    }
}
