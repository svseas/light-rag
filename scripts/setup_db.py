#!/usr/bin/env python3
"""Database setup script for LightRAG."""

import asyncio
import os
from pathlib import Path

import asyncpg
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/lightrag")


async def setup_database():
    """Set up the database schema and extensions."""
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        print("Setting up database extensions...")
        
        # Create extensions
        await conn.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
        await conn.execute('CREATE EXTENSION IF NOT EXISTS "vector"')
        await conn.execute('CREATE EXTENSION IF NOT EXISTS "pgrouting" CASCADE')
        
        print("Extensions created successfully!")
        
        # Check if tables exist
        result = await conn.fetch("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public' AND tablename = 'documents'
        """)
        
        if result:
            print("Database tables already exist.")
        else:
            print("Tables not found. Please run migration script:")
            print("psql -d lightrag -f migrations/001_create_tables.sql")
        
        # Test database connection
        await conn.execute("SELECT 1")
        print("Database connection successful!")
        
        await conn.close()
        
    except Exception as e:
        print(f"Database setup failed: {e}")
        return False
    
    return True


async def test_database():
    """Test database functionality."""
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        # Test vector operations
        await conn.execute("""
            CREATE TEMP TABLE test_vectors AS 
            SELECT '[1,2,3]'::vector as embedding
        """)
        
        result = await conn.fetchval("""
            SELECT embedding <-> '[1,2,4]'::vector 
            FROM test_vectors
        """)
        
        print(f"Vector distance test: {result}")
        
        # Test pgrouting
        await conn.execute("""
            CREATE TEMP TABLE test_edges (
                id SERIAL PRIMARY KEY,
                source BIGINT,
                target BIGINT,
                cost FLOAT
            )
        """)
        
        await conn.execute("""
            INSERT INTO test_edges (source, target, cost) VALUES
            (1, 2, 1.0),
            (2, 3, 1.5),
            (1, 3, 2.0)
        """)
        
        result = await conn.fetch("""
            SELECT * FROM pgr_dijkstra(
                'SELECT id, source, target, cost FROM test_edges',
                1, 3, FALSE
            )
        """)
        
        print(f"pgrouting test: {len(result)} path segments found")
        
        await conn.close()
        print("All database tests passed!")
        
    except Exception as e:
        print(f"Database test failed: {e}")
        return False
    
    return True


async def main():
    """Main setup function."""
    print("LightRAG Database Setup")
    print("=" * 30)
    
    success = await setup_database()
    if success:
        await test_database()
        print("\nDatabase setup completed successfully!")
    else:
        print("\nDatabase setup failed!")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(asyncio.run(main()))