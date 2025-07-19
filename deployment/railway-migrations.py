#!/usr/bin/env python3
"""
Railway Migration Script for LightRAG
Run this after deploying to Railway to set up the database schema
"""

import asyncio
import os
import sys
from pathlib import Path

import asyncpg


async def run_migrations():
    """Run all SQL migrations in order"""
    
    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)
    
    print(f"Connecting to database...")
    
    try:
        # Connect to database
        conn = await asyncpg.connect(database_url)
        
        # Get migrations directory
        migrations_dir = Path(__file__).parent.parent / 'migrations'
        
        if not migrations_dir.exists():
            print("ERROR: migrations directory not found")
            sys.exit(1)
        
        # Get all SQL files in order
        migration_files = sorted(migrations_dir.glob('*.sql'))
        
        if not migration_files:
            print("No migration files found")
            return
        
        print(f"Found {len(migration_files)} migration files")
        
        # Create migrations tracking table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version VARCHAR(255) PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Run each migration
        for migration_file in migration_files:
            version = migration_file.stem
            
            # Check if already applied
            result = await conn.fetchrow(
                "SELECT version FROM schema_migrations WHERE version = $1",
                version
            )
            
            if result:
                print(f"✓ Migration {version} already applied")
                continue
            
            print(f"Running migration: {version}")
            
            # Read and execute migration
            with open(migration_file, 'r') as f:
                sql = f.read()
            
            try:
                await conn.execute(sql)
                
                # Record migration as applied
                await conn.execute(
                    "INSERT INTO schema_migrations (version) VALUES ($1)",
                    version
                )
                
                print(f"✓ Migration {version} completed")
                
            except Exception as e:
                print(f"✗ Migration {version} failed: {e}")
                raise
        
        print("All migrations completed successfully!")
        
    except Exception as e:
        print(f"Error running migrations: {e}")
        sys.exit(1)
    
    finally:
        if 'conn' in locals():
            await conn.close()


async def setup_extensions():
    """Set up required PostgreSQL extensions"""
    
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("ERROR: DATABASE_URL environment variable not set")
        sys.exit(1)
    
    print("Setting up PostgreSQL extensions...")
    
    try:
        # Connect as superuser if possible
        conn = await asyncpg.connect(database_url)
        
        extensions = [
            'vector',      # pgvector for embeddings
            'pgrouting',   # pgrouting for graph operations
            'pg_trgm',     # trigram matching for fuzzy search
            'uuid-ossp',   # UUID generation
        ]
        
        for ext in extensions:
            try:
                await conn.execute(f'CREATE EXTENSION IF NOT EXISTS "{ext}"')
                print(f"✓ Extension {ext} enabled")
            except Exception as e:
                print(f"⚠ Extension {ext} could not be enabled: {e}")
                print(f"  You may need to install it manually or contact Railway support")
        
    except Exception as e:
        print(f"Error setting up extensions: {e}")
        print("You may need to run this manually or contact Railway support")
    
    finally:
        if 'conn' in locals():
            await conn.close()


async def main():
    """Main execution function"""
    print("🚀 Railway Migration Script for LightRAG")
    print("=" * 50)
    
    # Setup extensions first
    await setup_extensions()
    print()
    
    # Run migrations
    await run_migrations()
    print()
    
    print("🎉 Database setup complete!")
    print("Your LightRAG application should now be ready to use.")


if __name__ == "__main__":
    asyncio.run(main())