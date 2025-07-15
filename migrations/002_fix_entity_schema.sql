-- Fix entity table schema to match our models
-- Add missing columns and rename existing ones

-- Add confidence column
ALTER TABLE entities ADD COLUMN confidence FLOAT DEFAULT 0.0;

-- Rename columns to match our models
ALTER TABLE entities RENAME COLUMN name TO entity_name;
ALTER TABLE entities RENAME COLUMN type TO entity_type;
ALTER TABLE entities RENAME COLUMN properties_json TO metadata;

-- Update indexes to match new column names
DROP INDEX IF EXISTS idx_entities_name;
DROP INDEX IF EXISTS idx_entities_type;
CREATE INDEX idx_entities_entity_name ON entities(entity_name);
CREATE INDEX idx_entities_entity_type ON entities(entity_type);
CREATE INDEX idx_entities_confidence ON entities(confidence);

-- Create entity-to-node mapping table for pgrouting
CREATE TABLE entity_nodes (
    entity_id UUID PRIMARY KEY REFERENCES entities(id) ON DELETE CASCADE,
    node_id BIGINT UNIQUE NOT NULL
);

-- Create sequence for node IDs
CREATE SEQUENCE entity_node_id_seq START 1;

-- Create index for node mapping
CREATE INDEX idx_entity_nodes_node_id ON entity_nodes(node_id);

-- Function to get or create node ID for entity
CREATE OR REPLACE FUNCTION get_or_create_node_id(entity_uuid UUID)
RETURNS BIGINT AS $$
DECLARE
    node_id BIGINT;
BEGIN
    -- Try to get existing node ID
    SELECT en.node_id INTO node_id
    FROM entity_nodes en
    WHERE en.entity_id = entity_uuid;
    
    -- If not found, create new one
    IF node_id IS NULL THEN
        SELECT nextval('entity_node_id_seq') INTO node_id;
        INSERT INTO entity_nodes (entity_id, node_id) VALUES (entity_uuid, node_id);
    END IF;
    
    RETURN node_id;
END;
$$ LANGUAGE plpgsql;

-- Function to sync relationships to entity_edges for pgrouting
CREATE OR REPLACE FUNCTION sync_entity_edges()
RETURNS TRIGGER AS $$
DECLARE
    source_node_id BIGINT;
    target_node_id BIGINT;
    edge_cost FLOAT;
BEGIN
    IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
        -- Get or create node IDs for source and target entities
        source_node_id := get_or_create_node_id(NEW.source_entity_id);
        target_node_id := get_or_create_node_id(NEW.target_entity_id);
        
        -- Calculate cost based on confidence and weight
        edge_cost := (1.0 - COALESCE(NEW.confidence, 0.0)) * COALESCE(NEW.weight, 1.0);
        
        -- Insert or update entity_edges
        INSERT INTO entity_edges (source, target, cost, reverse_cost, relationship_id)
        VALUES (source_node_id, target_node_id, edge_cost, edge_cost, NEW.id)
        ON CONFLICT (relationship_id) DO UPDATE SET
            source = source_node_id,
            target = target_node_id,
            cost = edge_cost,
            reverse_cost = edge_cost;
            
        RETURN NEW;
    END IF;
    
    IF TG_OP = 'DELETE' THEN
        -- Remove from entity_edges
        DELETE FROM entity_edges WHERE relationship_id = OLD.id;
        RETURN OLD;
    END IF;
    
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically sync relationships to entity_edges
CREATE TRIGGER sync_relationships_to_edges
    AFTER INSERT OR UPDATE OR DELETE ON relationships
    FOR EACH ROW EXECUTE FUNCTION sync_entity_edges();

-- Add unique constraint to prevent duplicate relationships
ALTER TABLE relationships 
ADD CONSTRAINT unique_relationship 
UNIQUE (source_entity_id, target_entity_id, relationship_type, doc_id);

-- Update entity_edges to have unique constraint on relationship_id
ALTER TABLE entity_edges 
ADD CONSTRAINT unique_edge_relationship 
UNIQUE (relationship_id);

-- Create function to find shortest path between entities
CREATE OR REPLACE FUNCTION find_entity_path(
    source_entity_uuid UUID,
    target_entity_uuid UUID
) RETURNS TABLE (
    seq INTEGER,
    path_seq INTEGER,
    node BIGINT,
    edge BIGINT,
    cost FLOAT,
    agg_cost FLOAT
) AS $$
DECLARE
    source_node_id BIGINT;
    target_node_id BIGINT;
BEGIN
    -- Get node IDs for the entities
    SELECT node_id INTO source_node_id FROM entity_nodes WHERE entity_id = source_entity_uuid;
    SELECT node_id INTO target_node_id FROM entity_nodes WHERE entity_id = target_entity_uuid;
    
    -- If either entity not found, return empty
    IF source_node_id IS NULL OR target_node_id IS NULL THEN
        RETURN;
    END IF;
    
    -- Use pgr_dijkstra to find shortest path
    RETURN QUERY
    SELECT * FROM pgr_dijkstra(
        'SELECT id, source, target, cost, reverse_cost FROM entity_edges',
        source_node_id,
        target_node_id,
        directed := false
    );
END;
$$ LANGUAGE plpgsql;

-- Create function to get connected entities within N hops
CREATE OR REPLACE FUNCTION get_connected_entities(
    source_entity_uuid UUID,
    max_hops INTEGER DEFAULT 3
) RETURNS TABLE (
    entity_id UUID,
    entity_name VARCHAR(255),
    entity_type VARCHAR(50),
    hop_distance INTEGER,
    path_cost FLOAT
) AS $$
DECLARE
    source_node_id BIGINT;
BEGIN
    -- Get node ID for the source entity
    SELECT node_id INTO source_node_id FROM entity_nodes WHERE entity_id = source_entity_uuid;
    
    -- If entity not found, return empty
    IF source_node_id IS NULL THEN
        RETURN;
    END IF;
    
    -- Use pgr_drivingDistance to find entities within N hops
    RETURN QUERY
    SELECT 
        en.entity_id,
        e.entity_name,
        e.entity_type,
        dd.seq as hop_distance,
        dd.agg_cost as path_cost
    FROM pgr_drivingDistance(
        'SELECT id, source, target, cost, reverse_cost FROM entity_edges',
        source_node_id,
        max_hops,
        directed := false
    ) dd
    JOIN entity_nodes en ON dd.node = en.node_id
    JOIN entities e ON en.entity_id = e.id
    WHERE dd.node != source_node_id
    ORDER BY dd.agg_cost, e.entity_name;
END;
$$ LANGUAGE plpgsql;

-- Create function to calculate entity PageRank for importance scoring
CREATE OR REPLACE FUNCTION calculate_entity_pagerank()
RETURNS TABLE (
    entity_id UUID,
    entity_name VARCHAR(255),
    pagerank_score FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        en.entity_id,
        e.entity_name,
        pr.pagerank
    FROM pgr_pageRank(
        'SELECT id, source, target, cost, reverse_cost FROM entity_edges',
        directed := false
    ) pr
    JOIN entity_nodes en ON pr.node = en.node_id
    JOIN entities e ON en.entity_id = e.id
    ORDER BY pr.pagerank DESC;
END;
$$ LANGUAGE plpgsql;

-- Add comments for documentation
COMMENT ON TABLE entity_nodes IS 'Mapping table between entity UUIDs and pgrouting node IDs';
COMMENT ON FUNCTION get_or_create_node_id(UUID) IS 'Get or create a pgrouting node ID for an entity UUID';
COMMENT ON FUNCTION sync_entity_edges() IS 'Trigger function to sync relationships table to entity_edges for pgrouting';
COMMENT ON FUNCTION find_entity_path(UUID, UUID) IS 'Find shortest path between two entities using pgr_dijkstra';
COMMENT ON FUNCTION get_connected_entities(UUID, INTEGER) IS 'Get entities connected within N hops using pgr_drivingDistance';
COMMENT ON FUNCTION calculate_entity_pagerank() IS 'Calculate PageRank scores for all entities to determine importance';