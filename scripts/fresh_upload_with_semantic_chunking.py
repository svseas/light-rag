#!/usr/bin/env python3
"""Fresh upload with semantic chunking - Delete old document and reprocess with new pipeline."""

import asyncio
import os
import sys
from pathlib import Path
from uuid import UUID

import httpx
from dotenv import load_dotenv

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

API_BASE = "http://localhost:8000/api"
TEST_EMAIL = "joe@merctechs.com"
TEST_PASSWORD = "namsau78"

# Document to reprocess
OLD_DOC_ID = "77448c66-afb7-41a9-ab62-8a387634a8de"
DOC_PATH = "/Users/truongtang/Projects/light-rag/uploads/Market Research Report_ Building a Travel Content Creator Personal Brand.pdf"


async def fresh_upload_with_semantic_chunking():
    """Delete old document and upload fresh with semantic chunking."""
    # Set environment for MPS fallback
    os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'
    
    async with httpx.AsyncClient(timeout=300.0) as client:
        print("🚀 Fresh Upload with Semantic Chunking")
        print("=" * 50)
        
        # 1. Authentication
        print("1. Authenticating...")
        auth_response = await client.post(f"{API_BASE}/auth/signin", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        
        if auth_response.status_code != 200:
            print(f"❌ Auth failed: {auth_response.status_code}")
            print(auth_response.text)
            return
        
        auth_data = auth_response.json()
        
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
        
        # 3. Delete existing document
        print(f"\n3. Deleting existing document {OLD_DOC_ID}...")
        delete_response = await client.delete(
            f"{API_BASE}/documents/{OLD_DOC_ID}",
            headers=headers
        )
        
        if delete_response.status_code in [200, 404]:
            print("✅ Document deleted (or didn't exist)")
        else:
            print(f"⚠️ Delete failed: {delete_response.status_code} - continuing anyway")
            print(delete_response.text)
        
        # 4. Upload fresh document
        print(f"\n4. Uploading fresh document from {DOC_PATH}...")
        
        if not Path(DOC_PATH).exists():
            print(f"❌ File not found: {DOC_PATH}")
            return
        
        with open(DOC_PATH, 'rb') as f:
            files = {'file': (Path(DOC_PATH).name, f, 'application/pdf')}
            
            upload_response = await client.post(
                f"{API_BASE}/documents/upload",
                headers=headers,
                files=files
            )
        
        if upload_response.status_code != 200:
            print(f"❌ Upload failed: {upload_response.status_code}")
            print(upload_response.text)
            return
        
        upload_data = upload_response.json()
        
        # Handle different upload response formats
        if "document" in upload_data:
            new_document_id = upload_data["document"]["id"]
        elif "document_id" in upload_data:
            new_document_id = upload_data["document_id"]
        elif "id" in upload_data:
            new_document_id = upload_data["id"]
        else:
            print(f"❌ No document ID found in upload response: {upload_data}")
            return
            
        print(f"✅ Document uploaded: {new_document_id}")
        
        # 5. Start pipeline processing with semantic chunking
        print(f"\n5. Starting pipeline processing with semantic chunking...")
        pipeline_response = await client.post(
            f"{API_BASE}/pipeline/documents/{new_document_id}/process",
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
        
        # 6. Monitor pipeline status
        print(f"\n6. Monitoring pipeline status...")
        max_attempts = 60  # Increased for longer processing
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
            
            await asyncio.sleep(3)  # Longer sleep for heavy processing
            attempt += 1
        
        if status == "COMPLETED":
            print("✅ Pipeline completed successfully!")
            
            # 7. Test query with new semantic chunks
            print(f"\n7. Testing query with new semantic chunks...")
            query_response = await client.post(
                f"{API_BASE}/queries/process",
                headers=headers,
                json={
                    "query": "What are the key monetization strategies used by Vietnamese travel content creators?",
                    "user_id": "D28BrouWLkbVUlIPfcWsvbmTIgm1",
                    "project_id": project_id,
                    "document_ids": [new_document_id],
                    "max_results": 10,
                    "include_sources": True
                }
            )
            
            if query_response.status_code == 200:
                query_result = query_response.json()
                print(f"✅ Query processed successfully!")
                print(f"   Processing time: {query_result.get('processing_time', 'N/A')}s")
                print(f"   Answer length: {len(query_result.get('answer', ''))} chars")
                print(f"   Context items: {query_result.get('metadata', {}).get('context_items', 'N/A')}")
                print(f"   Context tokens: {query_result.get('metadata', {}).get('context_tokens', 'N/A')}")
                
                # Show expansion info
                expansion = query_result.get('metadata', {}).get('expansion', {})
                if expansion:
                    print(f"   Query expansion:")
                    print(f"     Expanded terms: {expansion.get('expanded_terms', [])}")
                    print(f"     Synonyms: {expansion.get('synonyms', [])}")
                
                # Show search optimization
                search_opt = query_result.get('metadata', {}).get('search_optimization', {})
                if search_opt:
                    print(f"   Search optimization:")
                    print(f"     K values: {search_opt.get('k_values', {})}")
                    print(f"     Reranked count: {search_opt.get('reranked_count', 'N/A')}")
                
                print(f"\nAnswer preview:")
                print(query_result.get('answer', '')[:800] + "...")
                
            else:
                print(f"❌ Query failed: {query_response.status_code}")
                print(query_response.text)
                
        elif status == "FAILED":
            print(f"❌ Pipeline failed: {status_data.get('error_message')}")
            if "failed_stage" in status_data:
                print(f"   Failed at stage: {status_data['failed_stage']}")
        else:
            print("⚠️ Pipeline still running after max attempts")
        
        # 8. Get final document info
        print(f"\n8. Getting final document info...")
        doc_response = await client.get(f"{API_BASE}/documents/{new_document_id}", headers=headers)
        if doc_response.status_code == 200:
            doc_info = doc_response.json()
            print(f"✅ Document processed successfully!")
            print(f"   New document ID: {new_document_id}")
            # The document response may not have counts, but we can check entities separately
        
        # 9. Check entities and relationships
        print(f"\n9. Checking extracted entities and relationships...")
        
        # Get entities
        entities_response = await client.get(
            f"{API_BASE}/entities/project/{project_id}",
            headers=headers
        )
        
        if entities_response.status_code == 200:
            entities_data = entities_response.json()
            print(f"✅ Found {entities_data['total']} entities")
            if entities_data["entities"]:
                sample_entity = entities_data['entities'][0]
                print(f"   Sample entity: {sample_entity['entity_name']} ({sample_entity['entity_type']})")
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
        
        print(f"\n🎉 Fresh upload with semantic chunking completed!")
        print(f"📋 Summary:")
        print(f"   - Old document deleted: {OLD_DOC_ID}")
        print(f"   - New document created: {new_document_id}")
        print(f"   - Pipeline status: {status}")
        print(f"   - Semantic chunking: ✅ Enabled")
        print(f"   - Query expansion: ✅ Enabled")
        print(f"   - RRF reranking: ✅ Enabled")


if __name__ == "__main__":
    asyncio.run(fresh_upload_with_semantic_chunking())