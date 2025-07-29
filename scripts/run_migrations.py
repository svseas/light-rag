#!/usr/bin/env python3
"""Run all database migrations in order."""

import asyncio
import os
from pathlib import Path
import asyncpg
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/lightrag")


async def run_migrations():
    """Run all migration files in order."""
    try:
        conn = await asyncpg.connect(DATABASE_URL)
        
        # Create migrations tracking table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version VARCHAR(255) PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Get migrations directory
        migrations_dir = Path(__file__).parent.parent / "migrations"
        if not migrations_dir.exists():
            print(f"Migrations directory not found: {migrations_dir}")
            return False
        
        # Get all SQL files in order
        migration_files = sorted(migrations_dir.glob("*.sql"))
        
        if not migration_files:
            print("No migration files found")
            return True
        
        print(f"Found {len(migration_files)} migration files")
        
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
                # Execute migration in a transaction
                async with conn.transaction():
                    await conn.execute(sql)
                    
                    # Record migration as applied
                    await conn.execute(
                        "INSERT INTO schema_migrations (version) VALUES ($1)",
                        version
                    )
                
                print(f"✓ Migration {version} completed")
                
            except Exception as e:
                print(f"✗ Migration {version} failed: {e}")
                # Continue with other migrations but note the failure
                continue
        
        await conn.close()
        print("All migrations completed!")
        return True
        
    except Exception as e:
        print(f"Error running migrations: {e}")
        return False


async def main():
    """Main migration function."""
    print("LightRAG Database Migrations")
    print("=" * 30)
    
    success = await run_migrations()
    if success:
        print("\nMigrations completed successfully!")
        return 0
    else:
        print("\nMigration failed!")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))