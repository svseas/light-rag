#!/usr/bin/env python3
"""Test script for form functionality."""

import asyncio
import httpx

BASE_URL = "http://localhost:8000"

async def test_forms():
    """Test form functionality."""
    async with httpx.AsyncClient(follow_redirects=True) as client:
        print("=== Testing Form Functionality ===")
        
        # Test 1: Check login form structure
        print("\n1. Testing login form structure...")
        response = await client.get(f"{BASE_URL}/login")
        print(f"GET /login: {response.status_code}")
        if response.status_code == 200:
            content = response.text
            if 'id="loginForm"' in content and 'type="submit"' in content:
                print("✓ Login form has correct structure")
            else:
                print("✗ Login form structure issues")
                
            if 'addEventListener' in content and 'preventDefault' in content:
                print("✓ Login form has JavaScript event handlers")
            else:
                print("✗ Login form missing JavaScript handlers")
        
        # Test 2: Check signup form structure
        print("\n2. Testing signup form structure...")
        response = await client.get(f"{BASE_URL}/signup")
        print(f"GET /signup: {response.status_code}")
        if response.status_code == 200:
            content = response.text
            if 'id="signupForm"' in content and 'type="submit"' in content:
                print("✓ Signup form has correct structure")
            else:
                print("✗ Signup form structure issues")
                
            if 'addEventListener' in content and 'preventDefault' in content:
                print("✓ Signup form has JavaScript event handlers")
            else:
                print("✗ Signup form missing JavaScript handlers")
        
        # Test 3: Check favicon
        print("\n3. Testing favicon...")
        response = await client.get(f"{BASE_URL}/login")
        if response.status_code == 200:
            content = response.text
            if 'data:image/svg+xml' in content:
                print("✓ Favicon is embedded (no 404 errors)")
            else:
                print("✗ Favicon not found in HTML")
        
        print("\n=== Form Tests Complete ===")
        print("\nNext steps:")
        print("1. Open browser dev tools (F12)")
        print("2. Go to http://localhost:8000/login")
        print("3. Try submitting the form")
        print("4. Check console for 'Login form submitted via JavaScript' message")
        print("5. Check Network tab - should NOT see GET requests with form data")

if __name__ == "__main__":
    asyncio.run(test_forms())