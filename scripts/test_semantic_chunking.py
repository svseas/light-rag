#!/usr/bin/env python3
"""Test semantic chunking with the travel document."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import asyncio
import asyncpg
from backend.agents.chunking import ChunkingAgent
from backend.models.chunks import ChunkingRequest
from backend.core.config import get_settings


async def test_semantic_chunking():
    """Test semantic chunking on the travel document."""
    settings = get_settings()
    
    # Connect to database
    conn = await asyncpg.connect(settings.database_url)
    
    try:
        # Get the travel document
        doc_id = '77448c66-afb7-41a9-ab62-8a387634a8de'
        row = await conn.fetchrow(
            "SELECT content_md FROM documents WHERE id = $1",
            doc_id
        )
        
        if not row:
            print("Document not found!")
            return
        
        content = row['content_md']
        print(f"Document length: {len(content)} characters")
        
        # Test both chunking methods
        print("\n=== TESTING TOKEN CHUNKER ===")
        token_agent = ChunkingAgent(use_semantic=False)
        token_request = ChunkingRequest(doc_id=doc_id, chunk_size=512, overlap=50)
        token_chunks = token_agent.chunk_document(content, token_request)
        
        print(f"Token chunks: {len(token_chunks)}")
        for i, chunk in enumerate(token_chunks[:3]):
            print(f"\nChunk {i+1} ({len(chunk)} chars):")
            print(chunk[:200] + "..." if len(chunk) > 200 else chunk)
        
        print("\n=== TESTING SEMANTIC CHUNKER ===")
        semantic_agent = ChunkingAgent(use_semantic=True)
        semantic_request = ChunkingRequest(doc_id=doc_id, chunk_size=1024)
        semantic_chunks = semantic_agent.chunk_document(content, semantic_request)
        
        print(f"Semantic chunks: {len(semantic_chunks)}")
        for i, chunk in enumerate(semantic_chunks[:3]):
            print(f"\nChunk {i+1} ({len(chunk)} chars):")
            print(chunk[:200] + "..." if len(chunk) > 200 else chunk)
        
        # Look for monetization information
        print("\n=== MONETIZATION INFORMATION ANALYSIS ===")
        
        def contains_monetization(chunk):
            keywords = ['monetization', 'revenue', 'income', 'affiliate', 'sponsor', 'brand', 'business']
            return any(keyword in chunk.lower() for keyword in keywords)
        
        token_monetization = [i for i, chunk in enumerate(token_chunks) if contains_monetization(chunk)]
        semantic_monetization = [i for i, chunk in enumerate(semantic_chunks) if contains_monetization(chunk)]
        
        print(f"Token chunks with monetization info: {len(token_monetization)} chunks")
        print(f"Semantic chunks with monetization info: {len(semantic_monetization)} chunks")
        
        # Show first monetization chunk from each method
        if token_monetization:
            print(f"\nFirst token monetization chunk (#{token_monetization[0]}):")
            print(token_chunks[token_monetization[0]][:500] + "...")
        
        if semantic_monetization:
            print(f"\nFirst semantic monetization chunk (#{semantic_monetization[0]}):")
            print(semantic_chunks[semantic_monetization[0]][:500] + "...")
        
        # Look for comprehensive monetization info
        def comprehensive_monetization(chunk):
            keywords = ['affiliate', 'sponsorship', 'revenue', 'income', 'business', 'brand']
            count = sum(1 for keyword in keywords if keyword in chunk.lower())
            return count >= 3
        
        token_comprehensive = [i for i, chunk in enumerate(token_chunks) if comprehensive_monetization(chunk)]
        semantic_comprehensive = [i for i, chunk in enumerate(semantic_chunks) if comprehensive_monetization(chunk)]
        
        print(f"\nToken chunks with comprehensive monetization info: {len(token_comprehensive)}")
        print(f"Semantic chunks with comprehensive monetization info: {len(semantic_comprehensive)}")
        
        if semantic_comprehensive:
            print(f"\nFirst comprehensive semantic monetization chunk (#{semantic_comprehensive[0]}):")
            print(semantic_chunks[semantic_comprehensive[0]][:800] + "...")
        
        if token_comprehensive:
            print(f"\nFirst comprehensive token monetization chunk (#{token_comprehensive[0]}):")
            print(token_chunks[token_comprehensive[0]][:800] + "...")
        
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(test_semantic_chunking())