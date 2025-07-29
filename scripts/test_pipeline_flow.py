#!/usr/bin/env python3
"""Test script for complete pipeline flow."""

import asyncio
import json
import os
import sys
from pathlib import Path
from uuid import uuid4

import httpx
from dotenv import load_dotenv

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

API_BASE = "http://localhost:8000/api"
TEST_EMAIL = "joe@merctechs.com"
TEST_PASSWORD = "namsau78"


async def test_pipeline_flow():
    """Test the complete pipeline flow."""
    async with httpx.AsyncClient() as client:
        print("🧪 Testing Complete Pipeline Flow")
        print("=" * 50)
        
        # 1. Test authentication
        print("1. Testing authentication...")
        auth_response = await client.post(f"{API_BASE}/auth/signin", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if auth_response.status_code != 200:
            print(f"❌ Auth failed: {auth_response.status_code}")
            print(auth_response.text)
            return
        
        auth_data = auth_response.json()
        print(f"Auth response: {auth_data}")
        
        # Handle different auth response formats
        if "access_token" in auth_data:
            token = auth_data["access_token"]
        elif "token" in auth_data:
            token = auth_data["token"]
        else:
            print(f"❌ No token found in auth response: {auth_data}")
            return
            
        headers = {"Authorization": f"Bearer {token}"}
        print("✅ Authentication successful")
        
        # 2. Get user project
        print("\n2. Getting user project...")
        project_response = await client.get(f"{API_BASE}/projects/me", headers=headers)
        
        if project_response.status_code != 200:
            print(f"❌ Project fetch failed: {project_response.status_code}")
            return
        
        project_data = project_response.json()
        project_id = project_data["id"]
        print(f"✅ Project ID: {project_id}")
        
        # 3. Upload a test document
        print("\n3. Uploading test document...")
        test_content = "Apple Inc. is a technology company founded by Steve Jobs in Cupertino, California. The company develops iPhones and MacBooks."
        
        upload_response = await client.post(
            f"{API_BASE}/documents/upload",
            headers=headers,
            files={"file": ("test.txt", test_content, "text/plain")}
        )
        
        if upload_response.status_code != 200:
            print(f"❌ Upload failed: {upload_response.status_code}")
            print(upload_response.text)
            return
        
        upload_data = upload_response.json()
        print(f"Upload response: {upload_data}")
        
        # Handle different upload response formats
        if "document" in upload_data:
            document_id = upload_data["document"]["id"]
        elif "document_id" in upload_data:
            document_id = upload_data["document_id"]
        elif "id" in upload_data:
            document_id = upload_data["id"]
        else:
            print(f"❌ No document ID found in upload response: {upload_data}")
            return
            
        print(f"✅ Document uploaded: {document_id}")
        
        # 4. Start pipeline processing
        print("\n4. Starting pipeline processing...")
        pipeline_response = await client.post(
            f"{API_BASE}/pipeline/documents/{document_id}/process",
            headers=headers
        )
        
        if pipeline_response.status_code != 200:
            print(f"❌ Pipeline start failed: {pipeline_response.status_code}")
            print(pipeline_response.text)
            return
        
        pipeline_data = pipeline_response.json()
        execution_id = pipeline_data["execution_id"]
        print(f"✅ Pipeline started: {execution_id}")
        print(f"   Status: {pipeline_data['status']}")
        print(f"   Current stage: {pipeline_data['current_stage']}")
        
        # 5. Monitor pipeline status
        print("\n5. Monitoring pipeline status...")
        max_attempts = 30
        attempt = 0
        
        while attempt < max_attempts:
            status_response = await client.get(
                f"{API_BASE}/pipeline/{execution_id}/status",
                headers=headers
            )
            
            if status_response.status_code != 200:
                print(f"❌ Status check failed: {status_response.status_code}")
                break
            
            status_data = status_response.json()
            status = status_data.get("status")
            current_stage = status_data.get("current_stage")
            progress = status_data.get("overall_progress", 0)
            
            print(f"   Attempt {attempt + 1}: {status} - {current_stage} ({progress:.1%})")
            
            if status in ["COMPLETED", "FAILED"]:
                break
            
            await asyncio.sleep(2)
            attempt += 1
        
        if status == "COMPLETED":
            print("✅ Pipeline completed successfully!")
        elif status == "FAILED":
            print(f"❌ Pipeline failed: {status_data.get('error_message')}")
        else:
            print("⚠️ Pipeline still running after max attempts")
        
        # 6. Test knowledge graph endpoints
        print("\n6. Testing knowledge graph endpoints...")
        
        # Get entities
        entities_response = await client.get(
            f"{API_BASE}/entities/project/{project_id}",
            headers=headers
        )
        
        if entities_response.status_code == 200:
            entities_data = entities_response.json()
            print(f"✅ Found {entities_data['total']} entities")
            if entities_data["entities"]:
                print(f"   Sample entity: {entities_data['entities'][0]['entity_name']} ({entities_data['entities'][0]['entity_type']})")
        else:
            print(f"❌ Entities fetch failed: {entities_response.status_code}")
        
        # Get relationships
        relationships_response = await client.get(
            f"{API_BASE}/relationships/project/{project_id}",
            headers=headers
        )
        
        if relationships_response.status_code == 200:
            relationships_data = relationships_response.json()
            print(f"✅ Found {relationships_data['total']} relationships")
            if relationships_data["relationships"]:
                rel = relationships_data['relationships'][0]
                print(f"   Sample relationship: {rel['source_entity']['entity_name']} -> {rel['target_entity']['entity_name']} ({rel['relationship_type']})")
        else:
            print(f"❌ Relationships fetch failed: {relationships_response.status_code}")
        
        # 7. Get project executions
        print("\n7. Getting project executions...")
        executions_response = await client.get(
            f"{API_BASE}/pipeline/project/{project_id}/executions",
            headers=headers
        )
        
        if executions_response.status_code == 200:
            executions_data = executions_response.json()
            print(f"✅ Found {len(executions_data)} pipeline executions")
        else:
            print(f"❌ Executions fetch failed: {executions_response.status_code}")
        
        print("\n🎉 Pipeline flow test completed!")


if __name__ == "__main__":
    asyncio.run(test_pipeline_flow())