#!/usr/bin/env python3
"""Test script for query processing system."""

import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Suppress logfire warnings for testing
os.environ["LOGFIRE_IGNORE_NO_CONFIG"] = "1"

from backend.models.queries import QueryProcessingRequest
from backend.services.query_service import get_query_service
from backend.core.database import get_db_pool


async def test_query_processing():
    """Test the complete query processing pipeline."""
    
    # Get query service
    query_service = await get_query_service()
    
    # Test queries
    test_queries = [
        "What are the main topics in the uploaded documents?",
        "Explain the key concepts and relationships",
        "What entities are mentioned most frequently?",
        "How are different concepts connected?",
        "Summarize the main findings"
    ]
    
    print("🚀 Testing Query Processing System")
    print("=" * 50)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 Test Query {i}: {query}")
        print("-" * 40)
        
        try:
            # Create request
            request = QueryProcessingRequest(
                query=query,
                max_results=5,
                include_sources=True
            )
            
            # Process query
            response = await query_service.process_query(request)
            
            print(f"✅ Processing Time: {response.processing_time:.2f}s")
            print(f"📊 Confidence: {response.confidence:.2f}")
            print(f"📚 Sources: {len(response.sources)}")
            print(f"💬 Answer: {response.answer[:200]}...")
            
            # Show metadata
            if response.metadata:
                print(f"🔍 Search Results: {response.metadata.get('search_results', {})}")
                print(f"🧩 Query Intent: {response.metadata.get('decomposition', {}).get('intent', 'unknown')}")
                print(f"🏷️ Entities: {response.metadata.get('decomposition', {}).get('entities', [])}")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")


async def test_individual_components():
    """Test individual query processing components."""
    
    print("\n🧪 Testing Individual Components")
    print("=" * 50)
    
    # Test query decomposition
    print("\n1. Query Decomposition")
    print("-" * 25)
    
    from backend.agents.query_decomposition import decompose_query
    
    test_query = "What are the main differences between Python and JavaScript for web development?"
    
    try:
        decomposition = await decompose_query(test_query)
        print(f"✅ Intent: {decomposition.intent}")
        print(f"🏷️ Entities: {decomposition.entities}")
        print(f"📋 Sub-queries: {[sq.text for sq in decomposition.sub_queries]}")
        print(f"🎯 Scope: {decomposition.scope}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    # Test search
    print("\n2. Search System")
    print("-" * 20)
    
    try:
        search_service = await get_query_service()
        search_results = await search_service.search_service.search_all(test_query, 3)
        
        print(f"✅ Total Results: {search_results.total_results}")
        print(f"📝 Keyword Results: {len(search_results.keyword_results)}")
        print(f"🔍 Semantic Results: {len(search_results.semantic_results)}")
        print(f"🕸️ Graph Results: {len(search_results.graph_results)}")
        
        # Show first result from each type
        if search_results.keyword_results:
            print(f"📝 First Keyword: {search_results.keyword_results[0].content[:100]}...")
        if search_results.semantic_results:
            print(f"🔍 First Semantic: {search_results.semantic_results[0].content[:100]}...")
        if search_results.graph_results:
            print(f"🕸️ First Graph: {search_results.graph_results[0].content[:100]}...")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")


async def main():
    """Main test function."""
    print("🔧 LightRAG Query System Test")
    print("=" * 40)
    
    await test_individual_components()
    await test_query_processing()


if __name__ == "__main__":
    asyncio.run(main())