#!/usr/bin/env python3
"""Test query performance with semantic chunking."""

import asyncio
import httpx
from dotenv import load_dotenv

load_dotenv()

async def test_query():
    async with httpx.AsyncClient(timeout=120.0) as client:
        # Login
        auth_response = await client.post('http://localhost:8000/api/auth/signin', json={
            'email': 'joe@merctechs.com',
            'password': 'namsau78'
        })
        
        auth_data = auth_response.json()
        print(f"Auth response: {auth_data}")
        
        # Handle different auth response formats
        if "access_token" in auth_data:
            token = auth_data["access_token"]
        elif "token" in auth_data:
            token = auth_data["token"]
        else:
            print(f"No token found in auth response")
            return
            
        headers = {'Authorization': f'Bearer {token}'}
        
        # Get project
        project_response = await client.get('http://localhost:8000/api/projects/me', headers=headers)
        project_id = project_response.json()['id']
        
        # Test query
        query_response = await client.post('http://localhost:8000/api/queries/process', headers=headers, json={
            'query': 'What are the latest monetization trends for travel content creators?',
            'user_id': 'D28BrouWLkbVUlIPfcWsvbmTIgm1',
            'project_id': project_id,
            'document_ids': ['757a63a0-fe51-4ffe-8e3d-4f8e6c264a79'],
            'max_results': 10,
            'include_sources': True
        }, timeout=120.0)
        
        if query_response.status_code == 200:
            result = query_response.json()
            print(f'✅ Query successful!')
            print(f'Processing time: {result.get("processing_time", "N/A")}s')
            print(f'Answer length: {len(result.get("answer", ""))} chars')
            print(f'Context items: {result.get("metadata", {}).get("context_items", "N/A")}')
            print(f'Context tokens: {result.get("metadata", {}).get("context_tokens", "N/A")}')
            
            # Show adaptive context info
            adaptive_context = result.get("metadata", {}).get("adaptive_context", {})
            if adaptive_context:
                print(f'\\n🧠 Adaptive Context:')
                print(f'   Complexity: {adaptive_context.get("complexity_level", "N/A")}')
                print(f'   Recommended tokens: {adaptive_context.get("recommended_tokens", "N/A")}')
                print(f'   Actual tokens: {adaptive_context.get("actual_tokens", "N/A")}')
                print(f'   Key factors: {adaptive_context.get("key_factors", [])}')
                print(f'   Reasoning: {adaptive_context.get("reasoning", "N/A")}')
            
            # Show search optimization with freshness info
            search_opt = result.get("metadata", {}).get("search_optimization", {})
            if search_opt:
                print(f'\\n🔍 Search Optimization:')
                print(f'   K values: {search_opt.get("k_values", {})}')
                print(f'   Reranked count: {search_opt.get("reranked_count", "N/A")}')
                
                # Show freshness information
                freshness_info = search_opt.get("freshness_info", {})
                if freshness_info:
                    print(f'\\n🕐 Freshness Scoring:')
                    print(f'   Temporal query detected: {freshness_info.get("temporal_query_detected", "N/A")}')
                    print(f'   Freshness weight: {freshness_info.get("freshness_weight", "N/A")}')
                    
                    sample_scores = freshness_info.get("sample_freshness_scores", [])
                    if sample_scores:
                        print(f'   Sample freshness scores:')
                        for i, score in enumerate(sample_scores[:2], 1):
                            print(f'     {i}. Source: {score.get("source", "N/A")[:8]}...')
                            print(f'        Category: {score.get("freshness_category", "N/A")}')
                            print(f'        Age: {score.get("age_days", "N/A")} days')
                            print(f'        Boost: {score.get("freshness_boost", "N/A")}')
                            print(f'        Original score: {score.get("original_score", "N/A")}')
                            print(f'        Boosted score: {score.get("boosted_score", "N/A")}')
                    else:
                        print(f'   No freshness scores available')
                
                # Show original results
                original_results = search_opt.get("original_results", {})
                if original_results:
                    print(f'   Original results: {original_results}')
            
            print(f'\\nAnswer preview:\\n{result.get("answer", "")[:800]}...')
        else:
            print(f'❌ Query failed: {query_response.status_code}')
            print(query_response.text)

if __name__ == "__main__":
    asyncio.run(test_query())