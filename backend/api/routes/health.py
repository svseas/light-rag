from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint.
    
    Returns:
        Health status.
    """
    return {"status": "healthy", "service": "light-rag"}