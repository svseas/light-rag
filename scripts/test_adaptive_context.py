#!/usr/bin/env python3
"""Test adaptive context window sizing with various query types."""

import asyncio
import httpx
from dotenv import load_dotenv

load_dotenv()

# Different query types to test adaptive context window
TEST_QUERIES = [
    {
        "query": "What is Facebook?",
        "expected_complexity": "simple",
        "description": "Simple factual query"
    },
    {
        "query": "What are the monetization strategies for Vietnamese travel content creators?",
        "expected_complexity": "moderate",
        "description": "Moderate explanatory query"
    },
    {
        "query": "Compare the effectiveness of affiliate marketing versus sponsored content for travel influencers, considering audience engagement and revenue potential",
        "expected_complexity": "complex",
        "description": "Complex comparative query"
    },
    {
        "query": "Analyze the evolution of Vietnamese travel content creation from 2020-2024, examining platform changes, audience behavior shifts, monetization trends, and the impact of COVID-19 on content strategies across different demographics",
        "expected_complexity": "highly_complex",
        "description": "Highly complex analytical query"
    }
]

async def test_adaptive_context():
    """Test adaptive context window sizing with various query types."""
    async with httpx.AsyncClient(timeout=120.0) as client:
        print("🧪 Testing Adaptive Context Window Sizing")
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
            print(f"   Query: {test_case['query'][:100]}...")
            print(f"   Expected complexity: {test_case['expected_complexity']}")
            
            # Process query
            query_response = await client.post('http://localhost:8000/api/queries/process', 
                headers=headers, 
                json={
                    'query': test_case['query'],
                    'user_id': 'D28BrouWLkbVUlIPfcWsvbmTIgm1',
                    'project_id': project_id,
                    'document_ids': [document_id],
                    'max_results': 10,
                    'include_sources': True
                }
            )
            
            if query_response.status_code == 200:
                result = query_response.json()
                
                # Extract adaptive context info
                adaptive_context = result.get('metadata', {}).get('adaptive_context', {})
                
                if adaptive_context:
                    complexity = adaptive_context.get('complexity_level', 'unknown')
                    recommended_tokens = adaptive_context.get('recommended_tokens', 'unknown')
                    actual_tokens = adaptive_context.get('actual_tokens', 'unknown')
                    key_factors = adaptive_context.get('key_factors', [])
                    reasoning = adaptive_context.get('reasoning', 'No reasoning provided')
                    
                    print(f"   ✅ Complexity: {complexity}")
                    print(f"   📏 Recommended tokens: {recommended_tokens}")
                    print(f"   📊 Actual tokens: {actual_tokens}")
                    print(f"   🔍 Key factors: {', '.join(key_factors)}")
                    print(f"   💭 Reasoning: {reasoning}")
                    
                    # Check if complexity matches expectation
                    if complexity == test_case['expected_complexity']:
                        print(f"   ✅ Complexity assessment matches expectation!")
                    else:
                        print(f"   ⚠️ Expected {test_case['expected_complexity']}, got {complexity}")
                    
                    # Show answer quality
                    answer_length = len(result.get('answer', ''))
                    print(f"   📝 Answer length: {answer_length} chars")
                    print(f"   ⏱️ Processing time: {result.get('processing_time', 0):.2f}s")
                    
                else:
                    print(f"   ❌ No adaptive context metadata found")
                    
            else:
                print(f"   ❌ Query failed: {query_response.status_code}")
                print(f"   Error: {query_response.text[:200]}...")
            
            print("-" * 60)
        
        print("\\n🎉 Adaptive Context Window Testing Complete!")

if __name__ == "__main__":
    asyncio.run(test_adaptive_context())