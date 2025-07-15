#!/usr/bin/env python3
"""Test script for project management functionality."""

import asyncio
import json
from datetime import datetime
import uuid

import httpx

BASE_URL = "http://localhost:8000"

# Create unique user for this test run
unique_id = str(uuid.uuid4())[:8]
TEST_USER = {
    "email": f"test{unique_id}@example.com",
    "password": "testpassword123"
}

async def test_project_management():
    """Test the complete project management workflow."""
    async with httpx.AsyncClient() as client:
        print("=== Testing Project Management System ===")
        
        # Test 1: Health check
        print("\n1. Testing health check...")
        response = await client.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        print("✓ Health check passed")
        
        # Test 2: Register user
        print(f"\n2. Testing user registration for {TEST_USER['email']}...")
        response = await client.post(f"{BASE_URL}/api/auth/signup", json=TEST_USER)
        signup_result = response.json()
        print(f"Signup response: {response.status_code}")
        
        if response.status_code == 200 and signup_result.get("success"):
            print("✓ User registered successfully")
        else:
            print(f"✗ Registration failed: {signup_result.get('message', 'Unknown error')}")
            return
        
        # Test 3: Login
        print("\n3. Testing user login...")
        response = await client.post(f"{BASE_URL}/api/auth/signin", json=TEST_USER)
        print(f"Login response: {response.status_code}")
        login_result = response.json()
        
        if response.status_code == 200 and login_result.get("success"):
            token = login_result.get("token")
            assert token is not None
            print("✓ Login successful")
        else:
            print(f"✗ Login failed: {login_result.get('message', 'Unknown error')}")
            return
        
        # Headers for authenticated requests
        headers = {"Authorization": f"Bearer {token}"}
        
        # Test 4: Create project
        print("\n4. Testing project creation...")
        project_data = {
            "name": "Test Project",
            "description": "A test project for demonstration"
        }
        response = await client.post(f"{BASE_URL}/api/projects/", json=project_data, headers=headers)
        print(f"Create project response: {response.status_code}")
        
        if response.status_code == 200:
            project = response.json()
            project_id = project["id"]
            print(f"✓ Project created: {project['name']}")
        elif response.status_code == 409:
            print("✓ User already has a project")
            # Get existing project
            response = await client.get(f"{BASE_URL}/api/projects/me", headers=headers)
            project = response.json()
            project_id = project["id"]
            print(f"✓ Retrieved existing project: {project['name']}")
        else:
            print(f"✗ Project creation failed: {response.status_code}")
            print(f"Response: {response.text}")
            return
        
        # Test 5: Get user's project
        print("\n5. Testing project retrieval...")
        response = await client.get(f"{BASE_URL}/api/projects/me", headers=headers)
        assert response.status_code == 200
        project = response.json()
        print(f"✓ Retrieved project: {project['name']}")
        
        # Test 6: Get project stats
        print("\n6. Testing project statistics...")
        response = await client.get(f"{BASE_URL}/api/projects/{project_id}/stats", headers=headers)
        assert response.status_code == 200
        stats = response.json()
        print(f"✓ Project stats: {stats['document_count']}/{stats['max_documents']} documents")
        print(f"  Total size: {stats['total_size_mb']} MB")
        print(f"  Can upload: {stats['can_upload']}")
        print(f"  Remaining slots: {stats['remaining_slots']}")
        
        # Test 7: Try to create another project (should fail)
        print("\n7. Testing project limit enforcement...")
        duplicate_project = {
            "name": "Another Project",
            "description": "This should fail"
        }
        response = await client.post(f"{BASE_URL}/api/projects/", json=duplicate_project, headers=headers)
        assert response.status_code == 409
        print("✓ Project limit enforced correctly")
        
        # Test 8: Update project
        print("\n8. Testing project update...")
        update_data = {
            "name": "Updated Test Project",
            "description": "Updated description"
        }
        response = await client.put(f"{BASE_URL}/api/projects/{project_id}", json=update_data, headers=headers)
        assert response.status_code == 200
        updated_project = response.json()
        print(f"✓ Project updated: {updated_project['name']}")
        
        print("\n=== All Project Management Tests Passed! ===")

if __name__ == "__main__":
    asyncio.run(test_project_management())