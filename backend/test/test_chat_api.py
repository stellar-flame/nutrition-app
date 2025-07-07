import asyncio
import json
import sys
import os

# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.chat import openai_chat
from database.schemas import ChatRequest, ChatResponse


async def test_chat_endpoint():
    """Test the chat API endpoint directly"""
    
    print("🧪 Testing Chat API Endpoint")
    print("="*60)
    
    # Test cases
    test_cases = [
        {
            "name": "Medium Apple",
            "description": "apple",
            "user_id": "test_user_123"
        },
        {
            "name": "Ambiguous food (should ask for clarification)",
            "description": "Greek yoghurt, chia seeds, granola, and honey",
            "user_id": "test_user_123"
        },
        {
            "name": "Banana small",
            "description": "banana",
            "user_id": "test_user_123"
        },
        {
            "name": "Complex meal (may fallback to AI)",
            "description": "grilled chicken, 100g",
            "user_id": "test_user_123"
        },
        {
            "name": "Complex meal (may fallback to AI)",
            "description": "grilled chicken salad with mixed greens",
            "user_id": "test_user_123"
        },
        {
            "name": "Ambiguous food (should ask for clarification)",
            "description": "bread",
            "user_id": "test_user_123"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}: {test_case['name']}")
        print("-" * 50)
        print(f"Input: '{test_case['description']}'")
        
        try:
            # Create request
            request = ChatRequest(
                description=test_case["description"],
                user_id=test_case["user_id"]
            )
            
            # Call the endpoint
            print("⏳ Calling chat endpoint...")
            response = await openai_chat(request)
            
            # Print response
            print("✅ Response received:")
            
            if hasattr(response, 'meals') and response.meals:
                print(f"📊 {len(response.meals)} Meal(s) found:")
                for i, meal in enumerate(response.meals, 1):
                    print(f"  Meal {i}:")
                    print(f"    Description: {meal.get('description', 'N/A')}")
                    print(f"    Calories: {meal.get('calories', 0)}")
                    print(f"    Protein: {meal.get('protein', 0)}g")
                    print(f"    Carbs: {meal.get('carbs', 0)}g")
                    print(f"    Fat: {meal.get('fat', 0)}g")
                    print(f"    Fiber: {meal.get('fiber', 0)}g")
                print(f"  Assumptions: {meal.get('assumptions', 'N/A')}")
                
            elif hasattr(response, 'message') and response.message:
                print("💬 Chat response:")
                print(f"  Message: {response.message}")
                
            if hasattr(response, 'conversation_id'):
                print(f"🔗 Conversation ID: {response.conversation_id}")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            print(f"   Type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
        
        print()


async def test_conversation_continuity():
    """Test conversation continuity with conversation_id"""
    
    print("\n" + "="*60)
    print("🔗 Testing Conversation Continuity")
    print("="*60)
    
    try:
        # First message
        print("\n📤 First message: 'apple'")
        request1 = ChatRequest(
            description="apple",
            user_id="test_user_456"
        )
        
        response1 = await openai_chat(request1)
        conversation_id = response1.conversation_id
        print(f"✅ Got conversation ID: {conversation_id}")
        
        # Follow-up message with conversation ID
        print(f"\n📤 Follow-up message: 'make it organic'")
        request2 = ChatRequest(
            description="make it organic",
            user_id="test_user_456",
            conversation_id=conversation_id
        )
        
        response2 = await openai_chat(request2)
        print(f"✅ Follow-up response received")
        print(f"🔗 Conversation ID: {response2.conversation_id}")
        
        if hasattr(response2, 'meal') and response2.meal:
            print("📊 Updated meal data received")
        elif hasattr(response2, 'message'):
            print(f"💬 Chat response: {response2.message}")
            
    except Exception as e:
        print(f"❌ Conversation test failed: {e}")
        import traceback
        traceback.print_exc()


async def test_usda_function_directly():
    """Test the USDA function directly"""
    
    print("\n" + "="*60)
    print("🧬 Testing USDA Function Directly")
    print("="*60)
    
    try:
        from api.chat import lookup_usda_nutrition
        
        test_foods = ["apple", "banana", "chicken breast"]
        
        for food in test_foods:
            print(f"\n🔍 Testing USDA lookup for: '{food}'")
            result = await lookup_usda_nutrition(food)
            
            if result.get("success"):
                print("✅ USDA lookup successful")
                data = result.get("data", {})
                print(f"  Description: {data.get('description', 'N/A')}")
                print(f"  Calories: {data.get('calories', 0)}")
                print(f"  Source: {data.get('assumptions', 'N/A')}")
            else:
                print(f"❌ USDA lookup failed: {result.get('error', 'Unknown error')}")
                
    except Exception as e:
        print(f"❌ Direct USDA test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🚀 Chat API Test Suite")
    print("="*60)
    
    # Test USDA function first
    # asyncio.run(test_usda_function_directly())
    
    # Test chat endpoint
    asyncio.run(test_chat_endpoint())
    
    # Test conversation continuity
    # asyncio.run(test_conversation_continuity())
    
    print("\n" + "="*60)
    print("✅ Chat API testing completed!")
