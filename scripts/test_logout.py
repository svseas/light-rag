#!/usr/bin/env python3
"""Test script for logout functionality."""

import asyncio
import httpx

BASE_URL = "http://localhost:8000"

async def test_logout():
    """Test logout functionality."""
    async with httpx.AsyncClient(follow_redirects=True) as client:
        print("=== Testing Logout Functionality ===")
        
        # Test 1: Check login page loads
        print("\n1. Testing login page accessibility...")
        response = await client.get(f"{BASE_URL}/login")
        print(f"GET /login: {response.status_code}")
        if response.status_code == 200:
            print("✓ Login page accessible")
        else:
            print(f"✗ Login page failed: {response.status_code}")
            return
        
        # Test 2: Check main app loads (should work even without auth for now)
        print("\n2. Testing main app accessibility...")
        response = await client.get(f"{BASE_URL}/")
        print(f"GET /: {response.status_code}")
        if response.status_code == 200:
            print("✓ Main app accessible")
            # Check if logout button exists in HTML
            if 'logoutLink' in response.text:
                print("✓ Logout link found in HTML")
            else:
                print("✗ Logout link not found in HTML")
        else:
            print(f"✗ Main app failed: {response.status_code}")
        
        # Test 3: Check JavaScript files load
        print("\n3. Testing JavaScript files...")
        response = await client.get(f"{BASE_URL}/static/js/auth.js")
        print(f"GET /static/js/auth.js: {response.status_code}")
        if response.status_code == 200:
            print("✓ Auth JS file loads")
            # Check if logout function exists
            if 'logout()' in response.text:
                print("✓ Logout function found in auth.js")
            else:
                print("✗ Logout function not found in auth.js")
        else:
            print(f"✗ Auth JS failed: {response.status_code}")
        
        response = await client.get(f"{BASE_URL}/static/js/app.js")
        print(f"GET /static/js/app.js: {response.status_code}")
        if response.status_code == 200:
            print("✓ App JS file loads")
        else:
            print(f"✗ App JS failed: {response.status_code}")
        
        print("\n=== Logout Test Complete ===")
        print("\nTo test logout manually:")
        print("1. Open http://localhost:8000/ in your browser")
        print("2. Click on the user profile dropdown (top right)")
        print("3. Click 'Logout'")
        print("4. Confirm the logout dialog")
        print("5. You should be redirected to the login page")

if __name__ == "__main__":
    asyncio.run(test_logout())