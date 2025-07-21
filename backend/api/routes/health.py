from fastapi import APIRouter

from backend.core.config import get_settings

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint.
    
    Returns:
        Health status.
    """
    return {"status": "healthy", "service": "light-rag", "version": "1.0.1"}


@router.get("/status")
async def service_status():
    """Service status endpoint showing configuration state.
    
    Returns:
        Service configuration status.
    """
    settings = get_settings()
    
    return {
        "service": "light-rag",
        "database_configured": bool(settings.database_url),
        "firebase_configured": bool(settings.firebase_api_key),
        "openrouter_configured": bool(settings.openrouter_api_key),
        "google_api_configured": bool(settings.google_api_key),
        "logfire_configured": bool(settings.logfire_token)
    }