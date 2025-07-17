-- Migration: Add query system tables
-- Timestamp: 2025-07-16 00:00:00

-- Query history table for storing user queries and responses
CREATE TABLE IF NOT EXISTS query_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(128),
    project_id UUID,
    query_text TEXT NOT NULL,
    response_text TEXT NOT NULL,
    context_used JSONB DEFAULT '{}',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for query history
CREATE INDEX IF NOT EXISTS idx_query_history_user_id ON query_history(user_id);
CREATE INDEX IF NOT EXISTS idx_query_history_project_id ON query_history(project_id);
CREATE INDEX IF NOT EXISTS idx_query_history_created_at ON query_history(created_at DESC);

-- Search results cache table for performance optimization
CREATE TABLE IF NOT EXISTS search_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    query_hash VARCHAR(64) UNIQUE NOT NULL,
    results JSONB NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for search cache
CREATE INDEX IF NOT EXISTS idx_search_cache_query_hash ON search_cache(query_hash);
CREATE INDEX IF NOT EXISTS idx_search_cache_expires_at ON search_cache(expires_at);

-- Enable pg_trgm extension for similarity search if not already enabled
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Add full-text search indexes for better keyword search performance
CREATE INDEX IF NOT EXISTS idx_chunks_content_fts ON chunks USING gin(to_tsvector('english', content));
CREATE INDEX IF NOT EXISTS idx_entities_name_fts ON entities USING gin(to_tsvector('english', entity_name));

-- Add similarity indexes for fuzzy matching
CREATE INDEX IF NOT EXISTS idx_entities_name_similarity ON entities USING gin(entity_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_chunks_content_similarity ON chunks USING gin(content gin_trgm_ops);