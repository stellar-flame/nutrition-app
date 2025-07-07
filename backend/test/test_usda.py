import asyncio
import json
import sys
import os

# Add parent directory to Python path to import usda_client
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client.usda_client import USDAClient


async def test_usda_api():
    """Test the USDA API client with various food queries"""
    
    try:
        # Initialize client
        client = USDAClient()
        print("✅ USDA Client initialized successfully")
        
        # Test foods to search for
        test_foods = [
            "apple raw",
            "banana medium",
            "chicken breast",
            "white rice cooked",
            "broccoli"
        ]
        
        for food in test_foods:
            print(f"\n🔍 Searching for: '{food}'")
            print("-" * 50)
            
            # Test search functionality
            search_results = await client.search_food(food, page_size=3)
            print(f"Found {len(search_results)} results")
            
            if search_results:
                # Show first few results
                for i, result in enumerate(search_results[:2]):
                    print(f"  {i+1}. {result.get('description', 'No description')}")
                    print(f"     FDC ID: {result.get('fdcId')}")
                    print(f"     Data Type: {result.get('dataType')}")
                
                # Test formatted meal data for first result
                print(f"\n📊 Formatted meal data for '{food}':")
                meal_data = await client.search_and_format(food)
                
                if meal_data:
                    print(json.dumps(meal_data, indent=2))
                else:
                    print("❌ Could not format meal data")
            else:
                print("❌ No results found")
        
        print("\n" + "="*60)
        print("✅ USDA API testing completed successfully!")
        
    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        print("💡 Make sure to set USDA_API_KEY in your .env file")
        print("   Get your free API key at: https://fdc.nal.usda.gov/api-key-signup.html")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")


async def test_specific_food():
    """Test with a specific food item for detailed inspection"""
    
    try:
        client = USDAClient()
        
        # Test with apple specifically
        food_query = "apple raw"
        print(f"🍎 Detailed test for: '{food_query}'")
        print("="*60)
        
        # Get search results
        results = await client.search_food(food_query, page_size=5)
        
        if results:
            print(f"Found {len(results)} results:")
            for i, result in enumerate(results):
                print(f"\n{i+1}. {result.get('description')}")
                print(f"   FDC ID: {result.get('fdcId')}")
                print(f"   Data Type: {result.get('dataType')}")
                
                # Get detailed nutrition for first result
                if i == 0:
                    print(f"\n📋 Getting detailed nutrition data...")
                    details = await client.get_food_details(str(result.get('fdcId')))
                    
                    if details:
                        print(f"✅ Retrieved detailed data")
                        
                        # Show key nutrients
                        nutrients = details.get('foodNutrients', [])
                        print(f"📊 Found {len(nutrients)} nutrients")
                        
                        # Show formatted meal data
                        meal_data = client.format_meal_data(details)
                        if meal_data:
                            print(f"\n🍽️ Formatted meal data:")
                            print(json.dumps(meal_data, indent=2))
        else:
            print("❌ No results found")
            
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("🧪 USDA API Client Test")
    print("="*60)
    
    # Run basic tests
    asyncio.run(test_usda_api())
    
    print("\n" + "="*60)
    
    # Run detailed test
    asyncio.run(test_specific_food())
