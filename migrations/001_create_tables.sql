-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pgrouting";

-- Create documents table
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    original_format VARCHAR(10) NOT NULL,
    content_md TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create document processing status table
CREATE TABLE document_processing (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    progress FLOAT DEFAULT 0.0,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create document metadata table
CREATE TABLE document_metadata (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    doc_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    summary TEXT,
    recursive_summary TEXT,
    entity_count INTEGER DEFAULT 0,
    chunk_count INTEGER DEFAULT 0,
    token_count INTEGER DEFAULT 0,
    metadata_json JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create chunks table with pgvector embeddings
CREATE TABLE chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    doc_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    embedding vector(3072), -- Google Gemini embedding dimension
    tokens INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create entities table with embeddings
CREATE TABLE entities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,
    doc_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_id UUID REFERENCES chunks(id) ON DELETE SET NULL,
    properties_json JSONB,
    embedding vector(3072), -- Google Gemini entity embedding
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create relationships table for graph operations
CREATE TABLE relationships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_entity_id UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    target_entity_id UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    relationship_type VARCHAR(100) NOT NULL,
    doc_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    confidence FLOAT DEFAULT 0.0,
    weight FLOAT DEFAULT 1.0, -- For pgrouting
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create edge table for pgrouting (required format)
CREATE TABLE entity_edges (
    id SERIAL PRIMARY KEY,
    source BIGINT NOT NULL,
    target BIGINT NOT NULL,
    cost FLOAT DEFAULT 1.0,
    reverse_cost FLOAT DEFAULT 1.0,
    relationship_id UUID REFERENCES relationships(id) ON DELETE CASCADE
);

-- Create queries table
CREATE TABLE queries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    query_text TEXT NOT NULL,
    decomposed_queries JSONB,
    context_sources JSONB,
    answer TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_documents_created_at ON documents(created_at);
CREATE INDEX idx_document_processing_document_id ON document_processing(document_id);
CREATE INDEX idx_document_processing_status ON document_processing(status);
CREATE INDEX idx_document_metadata_doc_id ON document_metadata(doc_id);
CREATE INDEX idx_chunks_doc_id ON chunks(doc_id);
CREATE INDEX idx_chunks_chunk_index ON chunks(doc_id, chunk_index);
CREATE INDEX idx_entities_doc_id ON entities(doc_id);
CREATE INDEX idx_entities_type ON entities(type);
CREATE INDEX idx_entities_name ON entities(name);
CREATE INDEX idx_relationships_source ON relationships(source_entity_id);
CREATE INDEX idx_relationships_target ON relationships(target_entity_id);
CREATE INDEX idx_relationships_doc_id ON relationships(doc_id);
CREATE INDEX idx_queries_created_at ON queries(created_at);

-- Create vector similarity indexes for pgvector
CREATE INDEX idx_chunks_embedding ON chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
CREATE INDEX idx_entities_embedding ON entities USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Create pgrouting indexes
CREATE INDEX idx_entity_edges_source ON entity_edges(source);
CREATE INDEX idx_entity_edges_target ON entity_edges(target);

-- Create updated_at triggers
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_documents_updated_at 
    BEFORE UPDATE ON documents 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_document_processing_updated_at 
    BEFORE UPDATE ON document_processing 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_document_metadata_updated_at 
    BEFORE UPDATE ON document_metadata 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();