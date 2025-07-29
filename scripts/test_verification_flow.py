#!/usr/bin/env python3
"""Test the complete verification flow."""

import asyncio
import httpx
import orjson
import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.config import get_settings

async def test_verification_flow():
    """Test the complete verification flow."""
    settings = get_settings()
    api_key = settings.firebase_api_key
    
    email = "joe@merctechs.com"
    password = "namsau78"
    
    print(f"=== Testing Complete Verification Flow for: {email} ===")
    
    async with httpx.AsyncClient() as client:
        # Step 1: Test signup (should send verification email)
        print("\n1. Testing signup to trigger verification email...")
        try:
            response = await client.post(
                "http://localhost:8000/api/auth/signup",
                json={"email": email, "password": password}
            )
            
            print(f"Signup response status: {response.status_code}")
            data = response.json()
            print(f"Signup response: {data}")
            
            if data.get("success"):
                print("✓ Signup successful - verification email should be sent")
            else:
                print(f"✗ Signup failed: {data.get('message')}")
                
        except Exception as e:
            print(f"✗ Signup test failed: {e}")
        
        # Step 2: Check verification status
        print("\n2. Checking verification status...")
        try:
            response = await client.post(
                "http://localhost:8000/api/auth/check-verification",
                json={"email": email}
            )
            
            print(f"Check verification response status: {response.status_code}")
            data = response.json()
            print(f"Verification status: {data}")
            
            if data.get("verified"):
                print("✓ Email is verified")
            else:
                print("✗ Email is NOT verified")
                
        except Exception as e:
            print(f"✗ Verification check failed: {e}")
        
        # Step 3: Test direct Firebase verification check
        print("\n3. Testing direct Firebase verification check...")
        try:
            # First get ID token
            signin_response = await client.post(
                f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}",
                content=orjson.dumps({
                    "email": email,
                    "password": password,
                    "returnSecureToken": True
                }),
                headers={"Content-Type": "application/json"}
            )
            
            if signin_response.status_code == 200:
                signin_data = orjson.loads(signin_response.content)
                print(f"Firebase email verified: {signin_data.get('emailVerified', False)}")
                
                # Get detailed user info
                lookup_response = await client.post(
                    f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={api_key}",
                    content=orjson.dumps({
                        "idToken": signin_data["idToken"]
                    }),
                    headers={"Content-Type": "application/json"}
                )
                
                if lookup_response.status_code == 200:
                    lookup_data = orjson.loads(lookup_response.content)
                    users = lookup_data.get("users", [])
                    
                    if users:
                        user = users[0]
                        print(f"Detailed Firebase user info:")
                        print(f"  - Email verified: {user.get('emailVerified', False)}")
                        print(f"  - Email: {user.get('email')}")
                        print(f"  - UID: {user.get('localId')}")
                        
                        # Check if there are any verification issues
                        if not user.get('emailVerified', False):
                            print("  ⚠️  Email still not verified in Firebase")
                            print("  This means the verification link hasn't been clicked or there's an issue")
                        else:
                            print("  ✓ Email is verified in Firebase")
                            
            else:
                print(f"Firebase signin failed: {signin_response.text}")
                
        except Exception as e:
            print(f"✗ Firebase verification check failed: {e}")
        
        # Step 4: Test login attempt
        print("\n4. Testing login attempt...")
        try:
            response = await client.post(
                "http://localhost:8000/api/auth/signin",
                json={"email": email, "password": password}
            )
            
            print(f"Login response status: {response.status_code}")
            data = response.json()
            print(f"Login response: {data}")
            
            if data.get("success"):
                print("✓ Login successful")
            else:
                print(f"✗ Login failed: {data.get('message')}")
                
        except Exception as e:
            print(f"✗ Login test failed: {e}")
        
        print("\n=== Verification Flow Test Complete ===")
        print("\nNext steps:")
        print("1. Check if verification email was actually sent to the user")
        print("2. Verify the verification link is working correctly")
        print("3. Check Firebase console for any configuration issues")

if __name__ == "__main__":
    asyncio.run(test_verification_flow())