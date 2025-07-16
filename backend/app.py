import logfire
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.api.main_routes import api_router
from backend.api.routes.frontend import router as frontend_router
from backend.core.config import configure_logfire, setup_directories


def create_app() -> FastAPI:
    """Create and configure FastAPI application.
    
    Returns:
        Configured FastAPI application.
    """
    # Configure logfire
    configure_logfire()
    
    # Create FastAPI app
    app = FastAPI(
        title="LightRAG API",
        description="A demonstration RAG system using PydanticAI and PostgreSQL",
        version="0.1.0",
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Instrument FastAPI with logfire
    logfire.instrument_fastapi(app)
    
    # Mount static files
    app.mount("/static", StaticFiles(directory="frontend/static"), name="static")
    
    # Include API routes
    app.include_router(api_router, prefix="/api")
    
    # Include frontend routes
    app.include_router(frontend_router)
    
    # Setup directories on startup
    @app.on_event("startup")
    async def startup_event():
        """Application startup event."""
        setup_directories()
        logfire.info("LightRAG API started successfully")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Application shutdown event."""
        logfire.info("LightRAG API shutting down")
    
    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "message": "LightRAG API",
            "version": "0.1.0",
            "docs": "/docs",
            "health": "/api/health",
        }
    
    return app


# Create app instance
app = create_app()