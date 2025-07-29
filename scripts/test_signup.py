#!/usr/bin/env python3
"""Test script for signup functionality."""

import asyncio
import httpx

BASE_URL = "http://localhost:8000"

async def test_signup():
    """Test signup functionality."""
    async with httpx.AsyncClient(follow_redirects=True) as client:
        print("=== Testing Signup Functionality ===")
        
        # Test 1: Check signup page loads
        print("\n1. Testing signup page...")
        response = await client.get(f"{BASE_URL}/signup")
        print(f"GET /signup: {response.status_code}")
        if response.status_code == 200:
            print("✓ Signup page loads successfully")
            # Check if page contains expected elements
            content = response.text
            if "Create your account" in content and "Create Account" in content:
                print("✓ Signup page contains expected content")
            else:
                print("✗ Signup page missing expected content")
        else:
            print(f"✗ Signup page failed: {response.status_code}")
        
        # Test 2: Check login page links to signup
        print("\n2. Testing login page signup link...")
        response = await client.get(f"{BASE_URL}/login")
        print(f"GET /login: {response.status_code}")
        if response.status_code == 200:
            content = response.text
            if 'href="/signup"' in content:
                print("✓ Login page contains signup link")
            else:
                print("✗ Login page missing signup link")
        else:
            print(f"✗ Login page failed: {response.status_code}")
        
        # Test 3: Test navigation flow
        print("\n3. Testing navigation between login and signup...")
        response = await client.get(f"{BASE_URL}/signup")
        if response.status_code == 200:
            content = response.text
            if 'href="/login"' in content:
                print("✓ Signup page contains login link")
            else:
                print("✗ Signup page missing login link")
        
        print("\n=== Signup Test Complete ===")
        print("\nTo test signup manually:")
        print("1. Open http://localhost:8000/signup in your browser")
        print("2. Fill out the signup form")
        print("3. Click 'Create Account'")
        print("4. Check that Firebase registration works")

if __name__ == "__main__":
    asyncio.run(test_signup())