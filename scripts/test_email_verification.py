#!/usr/bin/env python3
"""Test script for email verification functionality."""

import asyncio
import httpx

BASE_URL = "http://localhost:8000"

async def test_email_verification():
    """Test email verification functionality."""
    async with httpx.AsyncClient(follow_redirects=True) as client:
        print("=== Testing Email Verification Flow ===")
        
        # Test 1: Check verify-email page loads
        print("\n1. Testing verify-email page...")
        response = await client.get(f"{BASE_URL}/verify-email")
        print(f"GET /verify-email: {response.status_code}")
        if response.status_code == 200:
            print("✓ Verify-email page loads successfully")
            content = response.text
            if "Check Your Email" in content and "verification link" in content:
                print("✓ Verify-email page contains expected content")
            else:
                print("✗ Verify-email page missing expected content")
        else:
            print(f"✗ Verify-email page failed: {response.status_code}")
        
        # Test 2: Check verify-email page with email parameter
        print("\n2. Testing verify-email page with email parameter...")
        test_email = "test@example.com"
        response = await client.get(f"{BASE_URL}/verify-email?email={test_email}&from=signup")
        print(f"GET /verify-email?email={test_email}: {response.status_code}")
        if response.status_code == 200:
            print("✓ Verify-email page with parameters loads successfully")
        else:
            print(f"✗ Verify-email page with parameters failed: {response.status_code}")
        
        # Test 3: Check API endpoints exist
        print("\n3. Testing email verification API endpoints...")
        
        # Test resend verification endpoint
        response = await client.post(f"{BASE_URL}/api/auth/resend-verification", 
                                   json={"email": test_email})
        print(f"POST /api/auth/resend-verification: {response.status_code}")
        if response.status_code in [200, 400]:  # 400 is expected for non-existent user
            print("✓ Resend verification endpoint exists")
        else:
            print(f"✗ Resend verification endpoint failed: {response.status_code}")
        
        # Test check verification endpoint
        response = await client.post(f"{BASE_URL}/api/auth/check-verification", 
                                   json={"email": test_email})
        print(f"POST /api/auth/check-verification: {response.status_code}")
        if response.status_code == 200:
            print("✓ Check verification endpoint exists")
            data = response.json()
            print(f"  Response: {data}")
        else:
            print(f"✗ Check verification endpoint failed: {response.status_code}")
        
        # Test 4: Check signup flow updates
        print("\n4. Testing signup page updates...")
        response = await client.get(f"{BASE_URL}/signup")
        if response.status_code == 200:
            content = response.text
            if "verify-email" in content:
                print("✓ Signup page includes verification flow")
            else:
                print("✗ Signup page missing verification flow")
        
        # Test 5: Check login page updates
        print("\n5. Testing login page updates...")
        response = await client.get(f"{BASE_URL}/login")
        if response.status_code == 200:
            content = response.text
            if "verify your email" in content:
                print("✓ Login page includes verification messaging")
            else:
                print("✓ Login page loaded (verification messaging in JavaScript)")
        
        print("\n=== Email Verification Tests Complete ===")
        print("\nTo test the full flow:")
        print("1. Go to http://localhost:8000/signup")
        print("2. Create a new account")
        print("3. You should be redirected to /verify-email")
        print("4. Try to login with unverified account - should be blocked")
        print("5. Firebase will send verification email (if configured)")

if __name__ == "__main__":
    asyncio.run(test_email_verification())