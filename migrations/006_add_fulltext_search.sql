-- Add full-text search capabilities to chunks table
-- This migration adds tsvector columns and indexes for PostgreSQL full-text search

-- Add tsvector column for full-text search
ALTER TABLE chunks ADD COLUMN fts_vector tsvector;

-- Create function to update tsvector column
CREATE OR REPLACE FUNCTION update_chunk_fts_vector() RETURNS TRIGGER AS $$
BEGIN
    NEW.fts_vector = to_tsvector('english', COALESCE(NEW.content, ''));
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update fts_vector
CREATE TRIGGER update_chunk_fts_vector_trigger
    BEFORE INSERT OR UPDATE ON chunks
    FOR EACH ROW
    EXECUTE FUNCTION update_chunk_fts_vector();

-- Populate existing chunks with fts_vector
UPDATE chunks SET fts_vector = to_tsvector('english', COALESCE(content, ''));

-- Create GIN index for fast full-text search
CREATE INDEX idx_chunks_fts_vector ON chunks USING gin(fts_vector);

-- Add additional indexes for hybrid search optimization
CREATE INDEX idx_chunks_doc_id_fts ON chunks(doc_id) INCLUDE (fts_vector);
CREATE INDEX idx_chunks_project_id_fts ON chunks(project_id) INCLUDE (fts_vector);

-- Create query history table for conversation memory
CREATE TABLE IF NOT EXISTS query_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    session_id UUID NOT NULL,
    query_text TEXT NOT NULL,
    response_text TEXT,
    context_used JSONB,
    search_results JSONB,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for query history
CREATE INDEX idx_query_history_user_id ON query_history(user_id);
CREATE INDEX idx_query_history_project_id ON query_history(project_id);
CREATE INDEX idx_query_history_session_id ON query_history(session_id);
CREATE INDEX idx_query_history_created_at ON query_history(created_at);

-- Create search result cache table for performance
CREATE TABLE IF NOT EXISTS search_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    query_hash VARCHAR(64) NOT NULL,
    query_text TEXT NOT NULL,
    results JSONB NOT NULL,
    search_type VARCHAR(20) NOT NULL, -- 'hybrid', 'vector', 'fulltext', 'graph'
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for search cache
CREATE INDEX idx_search_cache_project_query ON search_cache(project_id, query_hash);
CREATE INDEX idx_search_cache_expires_at ON search_cache(expires_at);

-- Create trigger for updated_at on query_history
CREATE TRIGGER update_query_history_updated_at BEFORE UPDATE ON query_history
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create function for search result ranking
CREATE OR REPLACE FUNCTION hybrid_search_rank(
    fts_rank FLOAT,
    vector_similarity FLOAT,
    fts_weight FLOAT DEFAULT 0.3,
    vector_weight FLOAT DEFAULT 0.7
) RETURNS FLOAT AS $$
BEGIN
    RETURN (fts_rank * fts_weight) + (vector_similarity * vector_weight);
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Create function for reciprocal rank fusion
CREATE OR REPLACE FUNCTION reciprocal_rank_fusion(
    rank1 INTEGER,
    rank2 INTEGER,
    k INTEGER DEFAULT 60
) RETURNS FLOAT AS $$
BEGIN
    RETURN (1.0 / (k + rank1)) + (1.0 / (k + rank2));
END;
$$ LANGUAGE plpgsql IMMUTABLE;