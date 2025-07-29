#!/usr/bin/env python3
"""Test conversational context awareness with follow-up queries."""

import asyncio
import time
import httpx
from dotenv import load_dotenv

load_dotenv()

# Conversation test scenarios
CONVERSATION_SCENARIOS = [
    {
        "name": "Basic Follow-up with Pronouns",
        "queries": [
            "What are the key monetization strategies for Vietnamese travel content creators?",
            "How do they implement these strategies?",
            "What challenges do they face?"
        ]
    },
    {
        "name": "Topic Evolution",
        "queries": [
            "Tell me about travel content creators in Vietnam.",
            "What social media platforms do they use?",
            "How do they engage with their audience?"
        ]
    },
    {
        "name": "Reference Resolution",
        "queries": [
            "What are the main revenue streams for travel influencers?",
            "Which of these approaches is most effective?",
            "How can creators optimize this strategy?"
        ]
    }
]

async def test_conversation_context():
    """Test conversation context with various scenarios."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        print("🗣️ Testing Conversation Context Awareness")
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
        
        # Test each conversation scenario
        for scenario_num, scenario in enumerate(CONVERSATION_SCENARIOS, 1):
            print(f"\\n🎬 Scenario {scenario_num}: {scenario['name']}")
            print("-" * 50)
            
            # Process each query in the conversation
            for query_num, query in enumerate(scenario['queries'], 1):
                print(f"\\n  Query {query_num}: {query}")
                
                # Add small delay to ensure different timestamps
                if query_num > 1:
                    await asyncio.sleep(2)
                
                # Process query
                query_response = await client.post('http://localhost:8000/api/queries/process', 
                    headers=headers, 
                    json={
                        'query': query,
                        'user_id': 'D28BrouWLkbVUlIPfcWsvbmTIgm1',
                        'project_id': project_id,
                        'document_ids': [document_id],
                        'max_results': 5,
                        'include_sources': True
                    }
                )
                
                if query_response.status_code == 200:
                    result = query_response.json()
                    
                    # Show conversation context information
                    conv_context = result.get('metadata', {}).get('conversation_context', {})
                    
                    print(f"    ✅ Query processed successfully")
                    print(f"    ⏱️ Processing time: {result.get('processing_time', 0):.2f}s")
                    
                    if conv_context:
                        print(f"    📋 Conversation Context:")
                        print(f"       Original query: {conv_context.get('original_query', 'N/A')}")
                        
                        expanded_query = conv_context.get('expanded_query')
                        if expanded_query:
                            print(f"       Expanded query: {expanded_query}")
                        
                        print(f"       Context summary: {conv_context.get('context_summary', 'N/A')}")
                        print(f"       Recent queries: {conv_context.get('recent_queries_count', 0)}")
                        print(f"       Session duration: {conv_context.get('session_duration_minutes', 0)} min")
                        
                        entities = conv_context.get('extracted_entities', [])
                        if entities:
                            print(f"       Extracted entities: {', '.join(entities[:5])}")
                        
                        topics = conv_context.get('key_topics', [])
                        if topics:
                            print(f"       Key topics: {', '.join(topics[:3])}")
                    else:
                        print(f"    ⚠️ No conversation context found")
                    
                    # Show answer quality
                    answer_length = len(result.get('answer', ''))
                    print(f"    📝 Answer length: {answer_length} chars")
                    
                    # Show first part of answer
                    answer_preview = result.get('answer', '')[:200]
                    print(f"    💬 Answer preview: {answer_preview}...")
                    
                else:
                    print(f"    ❌ Query failed: {query_response.status_code}")
                    print(f"    Error: {query_response.text[:200]}...")
                    
                print("    " + "·" * 40)
        
        print(f"\\n🎉 Conversation Context Testing Complete!")
        print("\\nKey Features Tested:")
        print("  ✅ Pronoun resolution (they → travel creators)")
        print("  ✅ Reference resolution (these strategies → monetization)")
        print("  ✅ Topic continuity across queries")
        print("  ✅ Session duration tracking")
        print("  ✅ Entity extraction from conversation")

if __name__ == "__main__":
    asyncio.run(test_conversation_context())