#!/usr/bin/env python3
"""
Deployment Integration Tests
Tests the deployed API to ensure it's working correctly after deployment.
"""

import requests
import sys
import os
import time


class DeploymentTester:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'deployment-test/1.0'
        })
    
    def test_health_endpoint(self) -> bool:
        """Test the health check endpoint"""
        print("🏥 Testing health endpoint...")
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=20)
            
            if response.status_code != 200:
                print(f"❌ Health check failed with status {response.status_code}")
                return False
            
            data = response.json()
            
            # Verify expected fields
            if 'status' not in data or data['status'] != 'healthy':
                print(f"❌ Health check returned invalid status: {data}")
                return False
            
            print(f"✅ Health check passed: {data}")
            return True
            
        except Exception as e:
            print(f"❌ Health check failed with error: {e}")
            return False
    
    def test_root_endpoint(self) -> bool:
        """Test the root endpoint"""
        print("🏠 Testing root endpoint...")
        try:
            response = self.session.get(f"{self.base_url}/", timeout=10)
            
            if response.status_code != 200:
                print(f"❌ Root endpoint failed with status {response.status_code}")
                return False
            
            data = response.json()
            
            if 'status' not in data or data['status'] != 'healthy':
                print(f"❌ Root endpoint returned invalid response: {data}")
                return False
            
            print(f"✅ Root endpoint passed: {data}")
            return True
            
        except Exception as e:
            print(f"❌ Root endpoint failed with error: {e}")
            return False
    
    def test_chat_endpoint(self) -> bool:
        """Test the chat endpoint with a simple nutrition query"""
        print("💬 Testing chat endpoint...")
        try:
            # Simple test query
            payload = {
                "description": "Banana",
                "user_id": "test_user",
            }
            
            response = self.session.post(
                f"{self.base_url}/openai/chat", 
                json=payload, 
                timeout=300
            )
            
            if response.status_code != 200:
                print(f"❌ Chat endpoint failed with status {response.status_code}")
                print(f"Response: {response}")
                return False
            
            data = response.json()
            
            # Verify response structure
            required_fields = ['meals', 'conversation_id']
            for field in required_fields:
                if field not in data:
                    print(f"❌ Chat response missing field '{field}': {data}")
                    return False
            
            # Verify we got a meaningful response
            if not data['meals'] or len(data['meals']) == 0:
                print(f"❌ Chat response too short or empty: {data}")
                return False
            
            print(f"✅ Chat endpoint passed. Response length: {len(data['meals'])}")
            return True
            
        except Exception as e:
            print(f"❌ Chat endpoint failed with error: {e}")
            return False
    
    def test_invalid_endpoints(self) -> bool:
        """Test that invalid endpoints return appropriate 404s"""
        print("🚫 Testing invalid endpoints...")
        try:
            response = self.session.get(f"{self.base_url}/nonexistent", timeout=10)
            
            if response.status_code != 404:
                print(f"❌ Invalid endpoint should return 404, got {response.status_code}")
                return False
            
            print("✅ Invalid endpoints properly return 404")
            return True
            
        except Exception as e:
            print(f"❌ Invalid endpoint test failed with error: {e}")
            return False
    
    def run_all_tests(self) -> bool:
        """Run all deployment tests"""
        print(f"🚀 Starting deployment tests for: {self.base_url}")
        print("=" * 60)
        
        tests = [
            ("Health Check", self.test_health_endpoint),
            ("Root Endpoint", self.test_root_endpoint),
            ("Invalid Endpoints", self.test_invalid_endpoints),
            ("Chat Endpoint", self.test_chat_endpoint),  # Chat last as it's most complex
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n📋 Running: {test_name}")
            try:
                if test_func():
                    passed += 1
                else:
                    print(f"💥 Test '{test_name}' failed")
            except Exception as e:
                print(f"💥 Test '{test_name}' crashed: {e}")
        
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {passed}/{total} passed")
        
        if passed == total:
            print("🎉 All deployment tests passed!")
            return True
        else:
            print("💀 Some deployment tests failed!")
            return False


def main():
    """Main entry point for deployment tests"""
    
    # Handle help flag
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help', 'help']:
        print("Usage: python test_deployment.py <API_GATEWAY_URL>")
        print("   or: set API_GATEWAY_URL environment variable")
        print("\nExample:")
        print("  python test_deployment.py https://abc123.execute-api.us-east-1.amazonaws.com/prod")
        sys.exit(0)
    
    # Get API URL from environment or command line
    api_url = os.getenv('API_GATEWAY_URL')
    
    if len(sys.argv) > 1:
        api_url = sys.argv[1]
    
    if not api_url:
        print("❌ Error: API Gateway URL not provided")
        print("Usage: python test_deployment.py <API_GATEWAY_URL>")
        print("   or: set API_GATEWAY_URL environment variable")
        sys.exit(1)
    
    # Clean up URL
    api_url = api_url.rstrip('/')
    
    print(f"🎯 Target API: {api_url}")
    
    # Add a small delay to ensure Lambda is ready
    print("⏳ Waiting 10 seconds for Lambda to be ready...")
    time.sleep(10)
    
    # Run tests
    tester = DeploymentTester(api_url)
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
