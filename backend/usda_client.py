import httpx
import os
import json
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()


class USDAClient:
    """Client for USDA FoodData Central API"""
    
    def __init__(self):
        self.api_key = os.getenv("USDA_API_KEY")
        self.base_url = "https://api.nal.usda.gov/fdc/v1"
        
        if not self.api_key:
            raise ValueError("USDA_API_KEY not found in environment variables")
    
    async def search_food(self, query: str, page_size: int = 5) -> List[Dict]:
        """Search for foods in USDA database"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/foods/search",
                    params={
                        "api_key": self.api_key,
                        "query": query,
                        "pageSize": page_size,
                        "dataType": ["Foundation", "SR Legacy"]  # High quality data
                    },
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("foods", [])
                else:
                    print(f"USDA API Error: {response.status_code} - {response.text}")
                    return []
                    
        except Exception as e:
            print(f"Error searching USDA: {e}")
            return []
    
    async def get_food_details(self, fdc_id: str) -> Optional[Dict]:
        """Get detailed nutrition data for a specific food"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/food/{fdc_id}",
                    params={"api_key": self.api_key},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    print(f"USDA API Error: {response.status_code}")
                    return None
                    
        except Exception as e:
            print(f"Error getting food details: {e}")
            return None
    
    def format_meal_data(self, food_data: Dict) -> Optional[Dict]:
        """Convert USDA food data to meal format"""
        try:
            # Extract nutrients into a lookup dict
            nutrients = {}
            for nutrient in food_data.get("foodNutrients", []):
                name = nutrient.get("nutrient", {}).get("name", "")
                value = nutrient.get("amount", 0)
                nutrients[name] = value
            
            # Map USDA nutrients to our meal format
            meal_data = {
                "description": food_data.get("description", ""),
                "calories": nutrients.get("Energy", 0),
                "protein": nutrients.get("Protein", 0),
                "carbs": nutrients.get("Carbohydrate, by difference", 0),
                "fat": nutrients.get("Total lipid (fat)", 0),
                "fiber": nutrients.get("Fiber, total dietary", 0),
                "sugar": nutrients.get("Sugars, total including NLEA", 0),
                "assumptions": f"Data from USDA FoodData Central (FDC ID: {food_data.get('fdcId')})"
            }
            
            return meal_data
            
        except Exception as e:
            print(f"Error formatting meal data: {e}")
            return None
    
    async def search_and_format(self, query: str) -> Optional[Dict]:
        """Search for food and return formatted meal data"""
        foods = await self.search_food(query, page_size=1)
        
        if not foods:
            return None
            
        # Get detailed data for the first result
        food = foods[0]
        fdc_id = food.get("fdcId")
        
        if not fdc_id:
            return None
            
        detailed_food = await self.get_food_details(str(fdc_id))
        
        if not detailed_food:
            return None
            
        return self.format_meal_data(detailed_food)
