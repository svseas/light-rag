from uuid import UUID
import logging

import asyncpg

from backend.models.relationships import GraphPathResponse, GraphStatsResponse

logger = logging.getLogger(__name__)


class GraphService:
    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool

    async def find_shortest_path(self, source_entity_id: UUID, target_entity_id: UUID) -> GraphPathResponse:
        """Find shortest path between two entities using pgrouting."""
        async with self.db_pool.acquire() as conn:
            # Get node IDs
            source_node = await conn.fetchval("SELECT node_id FROM entity_nodes WHERE entity_id = $1", source_entity_id)
            target_node = await conn.fetchval("SELECT node_id FROM entity_nodes WHERE entity_id = $1", target_entity_id)
            
            if not source_node or not target_node:
                return self._empty_path_response(source_entity_id, target_entity_id)
            
            # Find shortest path
            query = """
                SELECT seq, node, edge, agg_cost
                FROM pgr_dijkstra(
                    'SELECT id, source, target, cost FROM entity_edges',
                    $1::bigint, $2::bigint, directed := false
                )
                ORDER BY seq
            """
            
            try:
                path_rows = await conn.fetch(query, source_node, target_node)
                
                if not path_rows:
                    return self._empty_path_response(source_entity_id, target_entity_id)
                
                # Convert nodes back to entity IDs
                path_entities = []
                for row in path_rows:
                    entity_id = await conn.fetchval("SELECT entity_id FROM entity_nodes WHERE node_id = $1", row['node'])
                    if entity_id:
                        path_entities.append(entity_id)
                
                return GraphPathResponse(
                    source_entity_id=source_entity_id,
                    target_entity_id=target_entity_id,
                    path_found=True,
                    path_length=len(path_entities) - 1,
                    path_cost=path_rows[-1]['agg_cost'],
                    path_entities=path_entities,
                    path_relationships=[]  # Simplified - just entities for now
                )
                
            except Exception as e:
                logger.error(f"Error finding path: {e}")
                return self._empty_path_response(source_entity_id, target_entity_id)

    async def get_connected_entities(self, entity_id: UUID, max_hops: int = 2) -> list[UUID]:
        """Get entities connected within max_hops using pgrouting."""
        async with self.db_pool.acquire() as conn:
            # Get node ID for the entity
            node_id = await conn.fetchval("SELECT node_id FROM entity_nodes WHERE entity_id = $1", entity_id)
            
            if not node_id:
                return []
            
            # Use pgrouting to find connected entities within max_hops
            query = """
                SELECT DISTINCT node
                FROM pgr_drivingDistance(
                    'SELECT id, source, target, cost FROM entity_edges',
                    $1::bigint, $2::float, directed := false
                )
                WHERE node != $1
            """
            
            try:
                connected_nodes = await conn.fetch(query, node_id, float(max_hops))
                
                # Convert node IDs back to entity IDs
                connected_entities = []
                for row in connected_nodes:
                    entity_id = await conn.fetchval("SELECT entity_id FROM entity_nodes WHERE node_id = $1", row['node'])
                    if entity_id:
                        connected_entities.append(entity_id)
                
                return connected_entities
                
            except Exception as e:
                logger.error(f"Error getting connected entities: {e}")
                return []

    async def get_graph_stats(self) -> GraphStatsResponse:
        """Get graph statistics."""
        async with self.db_pool.acquire() as conn:
            # Single query for efficiency
            stats_query = """
                SELECT 
                    (SELECT COUNT(*) FROM entities) as entity_count,
                    (SELECT COUNT(*) FROM relationships) as relationship_count,
                    (SELECT source_entity_id FROM relationships 
                     GROUP BY source_entity_id 
                     ORDER BY COUNT(*) DESC LIMIT 1) as most_connected
            """
            
            stats = await conn.fetchrow(stats_query)
            
            # Get relationship type distribution
            type_dist = await conn.fetch(
                "SELECT relationship_type, COUNT(*) as count FROM relationships GROUP BY relationship_type"
            )
            
            avg_relationships = 0.0
            if stats['entity_count'] > 0:
                avg_relationships = (stats['relationship_count'] * 2) / stats['entity_count']
            
            return GraphStatsResponse(
                total_entities=stats['entity_count'],
                total_relationships=stats['relationship_count'],
                avg_relationships_per_entity=avg_relationships,
                most_connected_entity=stats['most_connected'],
                relationship_type_distribution={row['relationship_type']: row['count'] for row in type_dist}
            )

    def _empty_path_response(self, source_entity_id: UUID, target_entity_id: UUID) -> GraphPathResponse:
        """Create empty path response (DRY helper)."""
        return GraphPathResponse(
            source_entity_id=source_entity_id,
            target_entity_id=target_entity_id,
            path_found=False,
            path_length=0,
            path_cost=0.0,
            path_entities=[],
            path_relationships=[]
        )