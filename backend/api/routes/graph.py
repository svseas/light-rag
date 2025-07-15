from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.core.dependencies import get_graph_service
from backend.models.relationships import GraphPathResponse, GraphStatsResponse
from backend.services.graph_service import GraphService

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/path/{source_entity_id}/{target_entity_id}", response_model=GraphPathResponse)
async def find_shortest_path(
    source_entity_id: UUID,
    target_entity_id: UUID,
    service: GraphService = Depends(get_graph_service),
) -> GraphPathResponse:
    """Find shortest path between two entities in the graph."""
    try:
        return await service.find_shortest_path(source_entity_id, target_entity_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to find path: {str(e)}")


@router.get("/connected/{entity_id}")
async def get_connected_entities(
    entity_id: UUID,
    max_hops: int = Query(2, ge=1, le=5, description="Maximum hops to traverse"),
    service: GraphService = Depends(get_graph_service),
) -> list[UUID]:
    """Get entities connected to the given entity within max_hops."""
    try:
        return await service.get_connected_entities(entity_id, max_hops)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get connected entities: {str(e)}")


@router.get("/stats", response_model=GraphStatsResponse)
async def get_graph_stats(
    service: GraphService = Depends(get_graph_service),
) -> GraphStatsResponse:
    """Get overall graph statistics."""
    try:
        return await service.get_graph_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get graph stats: {str(e)}")