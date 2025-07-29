#!/usr/bin/env python3
"""Test script for frontend functionality."""

import asyncio
import httpx

BASE_URL = "http://localhost:8000"

async def test_frontend():
    """Test frontend pages and functionality."""
    async with httpx.AsyncClient(follow_redirects=True) as client:
        print("=== Testing Frontend Pages ===")
        
        # Test 1: Login page
        print("\n1. Testing login page...")
        response = await client.get(f"{BASE_URL}/login")
        print(f"GET /login: {response.status_code}")
        if response.status_code == 200:
            print("✓ Login page loads successfully")
            # Check if page contains expected elements
            content = response.text
            if "LightRAG" in content and "Sign in" in content:
                print("✓ Login page contains expected content")
            else:
                print("✗ Login page missing expected content")
        else:
            print(f"✗ Login page failed: {response.status_code}")
        
        # Test 2: Static CSS file
        print("\n2. Testing static CSS file...")
        response = await client.get(f"{BASE_URL}/static/css/main.css")
        print(f"GET /static/css/main.css: {response.status_code}")
        if response.status_code == 200:
            print("✓ CSS file loads successfully")
        else:
            print(f"✗ CSS file failed: {response.status_code}")
        
        # Test 3: Static JS file
        print("\n3. Testing static JS files...")
        response = await client.get(f"{BASE_URL}/static/js/auth.js")
        print(f"GET /static/js/auth.js: {response.status_code}")
        if response.status_code == 200:
            print("✓ Auth JS file loads successfully")
        else:
            print(f"✗ Auth JS file failed: {response.status_code}")
        
        response = await client.get(f"{BASE_URL}/static/js/app.js")
        print(f"GET /static/js/app.js: {response.status_code}")
        if response.status_code == 200:
            print("✓ App JS file loads successfully")
        else:
            print(f"✗ App JS file failed: {response.status_code}")
        
        # Test 4: Main app page (should redirect to login without auth)
        print("\n4. Testing main app page...")
        response = await client.get(f"{BASE_URL}/")
        print(f"GET /: {response.status_code}")
        if response.status_code == 200:
            print("✓ Main app page loads successfully")
            # Check if page contains expected elements
            content = response.text
            if "LightRAG" in content and "app-container" in content:
                print("✓ Main app page contains expected content")
            else:
                print("✗ Main app page missing expected content")
        else:
            print(f"✗ Main app page failed: {response.status_code}")
        
        # Test 5: API health check
        print("\n5. Testing API health check...")
        response = await client.get(f"{BASE_URL}/api/health")
        print(f"GET /api/health: {response.status_code}")
        if response.status_code == 200:
            print("✓ API health check successful")
        else:
            print(f"✗ API health check failed: {response.status_code}")
        
        print("\n=== Frontend Tests Complete ===")

if __name__ == "__main__":
    asyncio.run(test_frontend())