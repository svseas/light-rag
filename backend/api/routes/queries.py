"""Query processing API endpoints."""

from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends
from backend.models.queries import (
    QueryProcessingRequest, QueryProcessingResponse, QueryHistory
)
from backend.services.query_service import get_query_service, QueryService


router = APIRouter(prefix="/queries", tags=["queries"])


@router.post("/process", response_model=QueryProcessingResponse)
async def process_query(
    request: QueryProcessingRequest,
    service: QueryService = Depends(get_query_service)
) -> QueryProcessingResponse:
    """Process user query through complete RAG pipeline.
    
    Args:
        request: Query processing request with user input.
        service: Query service instance.
        
    Returns:
        QueryProcessingResponse with answer and metadata.
        
    Raises:
        HTTPException: If query processing fails.
    """
    try:
        return await service.process_query(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")


@router.get("/history/{user_id}", response_model=list[QueryHistory])
async def get_user_query_history(
    user_id: UUID,
    limit: int = 50,
    service: QueryService = Depends(get_query_service)
) -> list[QueryHistory]:
    """Get query history for specific user.
    
    Args:
        user_id: User identifier.
        limit: Maximum number of queries to return.
        service: Query service instance.
        
    Returns:
        List of QueryHistory records.
        
    Raises:
        HTTPException: If retrieval fails.
    """
    try:
        return await service.get_query_history(user_id, limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get query history: {str(e)}")


@router.delete("/history/{user_id}/{query_id}")
async def delete_query_from_history(
    user_id: UUID,
    query_id: UUID,
    service: QueryService = Depends(get_query_service)
) -> dict[str, str]:
    """Delete specific query from user history.
    
    Args:
        user_id: User identifier.
        query_id: Query identifier to delete.
        service: Query service instance.
        
    Returns:
        Success message.
        
    Raises:
        HTTPException: If deletion fails or query not found.
    """
    try:
        deleted = await service.delete_query_history(user_id, query_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Query not found")
        return {"message": "Query deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete query: {str(e)}")


@router.post("/decompose")
async def decompose_query_endpoint(
    query: str
) -> dict:
    """Decompose query for analysis (debugging endpoint).
    
    Args:
        query: Query text to decompose.
        
    Returns:
        Query decomposition results.
        
    Raises:
        HTTPException: If decomposition fails.
    """
    try:
        from backend.agents.query_decomposition import decompose_query
        result = await decompose_query(query)
        return result.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query decomposition failed: {str(e)}")


@router.post("/search")
async def search_endpoint(
    query: str,
    limit: int = 10,
    service: QueryService = Depends(get_query_service)
) -> dict:
    """Search for relevant content (debugging endpoint).
    
    Args:
        query: Search query text.
        limit: Maximum results to return.
        service: Query service instance.
        
    Returns:
        Search results from multiple strategies.
        
    Raises:
        HTTPException: If search fails.
    """
    try:
        results = await service.search_service.search_all(query, limit)
        return results.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")