#!/usr/bin/env python3
"""Debug the signin response from Firebase."""

import asyncio
import httpx
import orjson
import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.config import get_settings

async def debug_signin_response():
    """Debug the signin response from Firebase."""
    settings = get_settings()
    api_key = settings.firebase_api_key
    
    email = "joe@merctechs.com"
    password = "namsau78"
    
    print(f"=== Debugging Firebase Sign-In Response for: {email} ===")
    
    async with httpx.AsyncClient() as client:
        # Test Firebase sign-in response
        print("\n1. Firebase signInWithPassword response...")
        try:
            response = await client.post(
                f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}",
                content=orjson.dumps({
                    "email": email,
                    "password": password,
                    "returnSecureToken": True
                }),
                headers={"Content-Type": "application/json"}
            )
            
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                data = orjson.loads(response.content)
                print(f"Response data keys: {list(data.keys())}")
                print(f"Raw emailVerified value: {data.get('emailVerified')}")
                print(f"Raw emailVerified type: {type(data.get('emailVerified'))}")
                print(f"Boolean check: {data.get('emailVerified', False)}")
                print(f"Full response: {data}")
                
                # Check if it's a string instead of boolean
                email_verified = data.get('emailVerified', False)
                if isinstance(email_verified, str):
                    print(f"⚠️  emailVerified is a string: '{email_verified}'")
                    print(f"String equals 'true': {email_verified == 'true'}")
                    print(f"String equals 'false': {email_verified == 'false'}")
                else:
                    print(f"emailVerified is boolean: {email_verified}")
                
            else:
                print(f"Error: {response.text}")
                
        except Exception as e:
            print(f"✗ Firebase signin failed: {e}")
        
        # Test with lookup for comparison
        print("\n2. Getting same user info via lookup...")
        try:
            # First get the token
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
                
                # Now lookup with the token
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
                        print(f"Lookup emailVerified: {user.get('emailVerified')}")
                        print(f"Lookup emailVerified type: {type(user.get('emailVerified'))}")
                        print(f"Lookup boolean check: {user.get('emailVerified', False)}")
                        
                        # Compare the two responses
                        signin_verified = signin_data.get('emailVerified', False)
                        lookup_verified = user.get('emailVerified', False)
                        
                        print(f"\n📊 Comparison:")
                        print(f"  SignIn emailVerified: {signin_verified} ({type(signin_verified)})")
                        print(f"  Lookup emailVerified: {lookup_verified} ({type(lookup_verified)})")
                        print(f"  Are they equal? {signin_verified == lookup_verified}")
                        
                        if signin_verified != lookup_verified:
                            print("  ⚠️  MISMATCH! SignIn and Lookup return different values")
                            print("  This is likely the source of the bug")
                
        except Exception as e:
            print(f"✗ Lookup test failed: {e}")
            
        print("\n=== Debug Complete ===")

if __name__ == "__main__":
    asyncio.run(debug_signin_response())