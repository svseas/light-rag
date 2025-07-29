#!/usr/bin/env python3
"""Test script for signup API."""

import asyncio
import httpx
import uuid

BASE_URL = "http://localhost:8000"

async def test_signup_api():
    """Test signup API directly."""
    async with httpx.AsyncClient(follow_redirects=True) as client:
        print("=== Testing Signup API ===")
        
        # Create a unique test user
        unique_id = str(uuid.uuid4())[:8]
        test_email = f"test{unique_id}@example.com"
        test_password = "testpass123"
        
        print(f"Testing with email: {test_email}")
        
        # Test 1: Check signup endpoint
        print("\n1. Testing signup API endpoint...")
        try:
            response = await client.post(f"{BASE_URL}/api/auth/signup", 
                                       json={"email": test_email, "password": test_password})
            print(f"POST /api/auth/signup: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Response data: {data}")
                
                if data.get("success"):
                    print("✓ Signup successful")
                else:
                    print(f"✗ Signup failed: {data.get('message')}")
            else:
                print(f"✗ Signup failed with status {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"✗ Signup request failed: {e}")
        
        # Test 2: Test validation
        print("\n2. Testing validation...")
        try:
            response = await client.post(f"{BASE_URL}/api/auth/signup", 
                                       json={"email": "invalid-email", "password": "123"})
            print(f"POST /api/auth/signup (invalid): {response.status_code}")
            
            if response.status_code == 422:
                print("✓ Validation working correctly")
            else:
                data = response.json()
                print(f"Response: {data}")
                
        except Exception as e:
            print(f"✗ Validation test failed: {e}")
        
        # Test 3: Test duplicate email
        print("\n3. Testing duplicate email...")
        try:
            response = await client.post(f"{BASE_URL}/api/auth/signup", 
                                       json={"email": test_email, "password": test_password})
            print(f"POST /api/auth/signup (duplicate): {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Response: {data}")
                
                if not data.get("success"):
                    print("✓ Duplicate email handling working")
                else:
                    print("✗ Duplicate email not handled properly")
            else:
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"✗ Duplicate email test failed: {e}")
        
        print("\n=== Signup API Tests Complete ===")

if __name__ == "__main__":
    asyncio.run(test_signup_api())