#!/usr/bin/env python3
"""
Test client for the OpenAI chat endpoint
Usage: python test_chat_client.py
"""

import asyncio
import requests
import json
import sys
from typing import Optional
import os

# Add parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.chat import openai_chat
from database.schemas import ChatRequest, ChatResponse


# API Configuration

class ChatClient:
    def __init__(self):
        self.history: Optional[list] = None

    async def chat(self, description: str) -> dict:
        """Send a chat message to the API"""
   
        try:
            # Create request
            request = ChatRequest(
                description=description,
                user_id="test_user",
                history=self.history
            )
            
            # Call the endpoint
            print("⏳ Calling chat endpoint...")
            response = await openai_chat(request)

            # Print response
            print("✅ Response received:")
            return response

        except Exception as e:
            print(f"❌ Error: {e}")
            print(f"   Type: {type(e).__name__}")
            import traceback
            traceback.print_exc()
        
    
    def print_response(self, response: ChatResponse):
        """Pretty print the API response"""
        print("\n" + "="*50)
        print("🤖 API RESPONSE")
        print("="*50)
        
        if "error" in response:
            print(f"❌ Error: {response['error']}")
            return
        
        # Print conversation ID
        if response.conversation_id:
            print(f"💬 Conversation ID: {response.conversation_id}")

        # Print message if present
        if response.message:
            print(f"📝 Message: {response.message}")

        # Print meals if present
        if response.meals:
            print(f"🍽️  Found {len(response.meals)} meal(s):")
            for i, meal in enumerate(response.meals, 1):
                print(f"\n  Meal {i}:")
                print(f"    📋 Description: {meal.get('description', 'N/A')}")
                print(f"    🔥 Calories: {meal.get('calories', 0)}")
                print(f"    🥩 Protein: {meal.get('protein', 0)}g")
                print(f"    🍞 Carbs: {meal.get('carbs', 0)}g")
                print(f"    🥑 Fat: {meal.get('fat', 0)}g")
                print(f"    🌾 Fiber: {meal.get('fiber', 0)}g")
                print(f"    🍯 Sugar: {meal.get('sugar', 0)}g")
                print(f"    🧮 Quantity: {meal.get('quantity', 'N/A')}")
                if meal.get('assumptions'):
                    print(f"    💭 Assumptions: {meal['assumptions']}")

        if response.errors:
            print(f"📝 Errors found:")
            for error in response.errors:
                print(f"   - {error}")

        print("="*50 + "\n")

async def interactive_mode():
    """Run interactive chat session"""
    client = ChatClient()
    
    print("🍎 Nutrition AI Chat Client")
    print("="*40)
    print("Type 'quit' or 'exit' to stop")
    print("Type 'reset' to start a new conversation")
    print("="*40 + "\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit']:
                print("👋 Goodbye!")
                break
            
            if user_input.lower() == 'reset':
                print("🔄 Conversation reset\n")
                client.history = []
                continue
            
            if not user_input:
                continue

            response = await client.chat(user_input)
            client.history = response.history or []
            client.print_response(response)
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
     asyncio.run(interactive_mode())
