import httpx
import os
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
                    print(f"USDA search results for '{query}': {len(data.get('foods', []))} items found")
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
