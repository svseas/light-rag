#!/usr/bin/env python3
"""Debug Firebase user data."""

import asyncio
import httpx
import orjson
import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.config import get_settings

async def debug_firebase_user():
    """Debug Firebase user data."""
    settings = get_settings()
    api_key = settings.firebase_api_key
    
    email = "joe@merctechs.com"
    
    print(f"=== Debugging Firebase User: {email} ===")
    
    async with httpx.AsyncClient() as client:
        # Check user data by trying to sign in
        print("\n1. Trying to sign in to get user data...")
        try:
            response = await client.post(
                f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}",
                content=orjson.dumps({
                    "email": email,
                    "password": "namsau78",
                    "returnSecureToken": True
                }),
                headers={"Content-Type": "application/json"}
            )
            
            print(f"Sign-in response status: {response.status_code}")
            
            if response.status_code == 200:
                data = orjson.loads(response.content)
                print(f"User found in Firebase:")
                print(f"  - UID: {data.get('localId')}")
                print(f"  - Email: {data.get('email')}")
                print(f"  - Email Verified: {data.get('emailVerified', False)}")
                print(f"  - ID Token: {data.get('idToken')[:50]}...")
                print(f"  - Refresh Token: {data.get('refreshToken')[:50]}...")
                
                # Check if email is verified
                if data.get('emailVerified', False):
                    print("✓ Email is verified in Firebase")
                    
                    # Now try to get user info with the ID token
                    print("\n2. Getting user info with ID token...")
                    try:
                        lookup_response = await client.post(
                            f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={api_key}",
                            content=orjson.dumps({
                                "idToken": data.get('idToken')
                            }),
                            headers={"Content-Type": "application/json"}
                        )
                        
                        print(f"Lookup response status: {lookup_response.status_code}")
                        
                        if lookup_response.status_code == 200:
                            lookup_data = orjson.loads(lookup_response.content)
                            users = lookup_data.get("users", [])
                            
                            if users:
                                user = users[0]
                                print(f"Detailed user info:")
                                print(f"  - Email Verified: {user.get('emailVerified', False)}")
                                print(f"  - Last Login: {user.get('lastLoginAt')}")
                                print(f"  - Created: {user.get('createdAt')}")
                                print(f"  - Provider: {user.get('providerUserInfo', [])}")
                        else:
                            print(f"Lookup failed: {lookup_response.text}")
                            
                    except Exception as e:
                        print(f"Lookup failed: {e}")
                        
                else:
                    print("✗ Email is NOT verified in Firebase")
                    print("This means the user has not clicked the verification link yet.")
            else:
                error_data = orjson.loads(response.content)
                print(f"✗ Lookup failed: {error_data}")
                
        except Exception as e:
            print(f"✗ Error checking Firebase: {e}")

if __name__ == "__main__":
    asyncio.run(debug_firebase_user())