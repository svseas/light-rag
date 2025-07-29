#!/usr/bin/env python3
"""Test document freshness scoring with various query types."""

import asyncio
import httpx
from dotenv import load_dotenv

load_dotenv()

# Different query types to test freshness scoring
TEST_QUERIES = [
    {
        "query": "What is Facebook?",
        "description": "Non-temporal query (should have minimal freshness boost)",
        "expected_boost": "minimal"
    },
    {
        "query": "What are the latest monetization trends for travel content creators?",
        "description": "Temporal query (should have significant freshness boost)",
        "expected_boost": "significant"
    },
    {
        "query": "Recent changes in Vietnamese social media platforms",
        "description": "Temporal query with 'recent' keyword",
        "expected_boost": "significant"
    },
    {
        "query": "Current travel content creator strategies in 2024",
        "description": "Temporal query with 'current' and year",
        "expected_boost": "significant"
    }
]

async def test_freshness_scoring():
    """Test freshness scoring with various query types."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        print("🕐 Testing Document Freshness Scoring")
        print("=" * 60)
        
        # Login
        auth_response = await client.post('http://localhost:8000/api/auth/signin', json={
            'email': 'joe@merctechs.com',
            'password': 'namsau78'
        })
        
        if auth_response.status_code != 200:
            print(f"❌ Authentication failed: {auth_response.status_code}")
            return
        
        token = auth_response.json()['token']
        headers = {'Authorization': f'Bearer {token}'}
        
        # Get project
        project_response = await client.get('http://localhost:8000/api/projects/me', headers=headers)
        if project_response.status_code != 200:
            print(f"❌ Project fetch failed: {project_response.status_code}")
            return
        
        project_id = project_response.json()['id']
        document_id = '757a63a0-fe51-4ffe-8e3d-4f8e6c264a79'
        
        # Test each query type
        for i, test_case in enumerate(TEST_QUERIES, 1):
            print(f"\\n{i}. {test_case['description']}")
            print(f"   Query: {test_case['query']}")
            print(f"   Expected boost: {test_case['expected_boost']}")
            
            # Process query
            query_response = await client.post('http://localhost:8000/api/queries/process', 
                headers=headers, 
                json={
                    'query': test_case['query'],
                    'user_id': 'D28BrouWLkbVUlIPfcWsvbmTIgm1',
                    'project_id': project_id,
                    'document_ids': [document_id],
                    'max_results': 5,
                    'include_sources': True
                }
            )
            
            if query_response.status_code == 200:
                result = query_response.json()
                
                # Check if we got search results with freshness info
                search_optimization = result.get('metadata', {}).get('search_optimization', {})
                
                print(f"   ✅ Query processed successfully")
                print(f"   ⏱️ Processing time: {result.get('processing_time', 0):.2f}s")
                
                # Look for freshness info in metadata
                found_freshness = False
                if 'sources' in result:
                    for source in result['sources']:
                        if isinstance(source, dict) and 'freshness_score' in source:
                            found_freshness = True
                            print(f"   📅 Freshness score: {source.get('freshness_score', 'N/A')}")
                            print(f"   🏷️ Freshness category: {source.get('freshness_category', 'N/A')}")
                            print(f"   📈 Original score: {source.get('original_score', 'N/A')}")
                            print(f"   🚀 Freshness boost: {source.get('freshness_boost', 'N/A')}")
                            print(f"   📝 Age: {source.get('age_days', 'N/A')} days")
                            break
                
                if not found_freshness:
                    print(f"   ⚠️ No freshness information found in response")
                
                # Show answer quality
                answer_length = len(result.get('answer', ''))
                print(f"   📝 Answer length: {answer_length} chars")
                    
            else:
                print(f"   ❌ Query failed: {query_response.status_code}")
                print(f"   Error: {query_response.text[:200]}...")
            
            print("-" * 60)
        
        print("\\n🎉 Freshness Scoring Testing Complete!")

if __name__ == "__main__":
    asyncio.run(test_freshness_scoring())