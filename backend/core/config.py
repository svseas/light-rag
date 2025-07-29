import os
from functools import lru_cache
from typing import Optional

import logfire
from openai import OpenAI
from pydantic import BaseModel
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Configuration
    openrouter_api_key: str = ""
    logfire_token: str = ""
    
    # OpenAI Configuration (for PydanticAI with OpenRouter)
    openai_api_key: str = ""
    openai_base_url: str = "https://openrouter.ai/api/v1"
    
    # Google Gemini Configuration
    google_api_key: str = ""
    
    # Firebase Authentication Configuration
    firebase_api_key: str = ""
    firebase_auth_domain: str = ""
    firebase_project_id: str = ""
    firebase_storage_bucket: str = ""
    firebase_messaging_sender_id: str = ""
    firebase_app_id: str = ""
    firebase_measurement_id: str = ""
    firebase_private_key_id: str = ""
    firebase_private_key: str = ""
    firebase_client_email: str = ""
    firebase_client_id: str = ""
    firebase_auth_uri: str = "https://accounts.google.com/o/oauth2/auth"
    firebase_token_uri: str = "https://oauth2.googleapis.com/token"
    
    # Database Configuration
    database_url: str = ""
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    postgres_db: str = "lightrag"
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379"
    
    # Elasticsearch Configuration
    elasticsearch_url: str = "http://localhost:9200"
    
    # Application Configuration
    debug: bool = True
    secret_key: str = "your-secret-key-here"
    allowed_hosts: str = "localhost,127.0.0.1"
    
    # PydanticAI Configuration
    default_model: str = "claude-3.5-sonnet"
    embedding_model: str = "gemini-embedding-001"
    
    # File Upload Configuration
    max_file_size: int = 5242880  # 5MB for project limits
    upload_path: str = "./uploads"
    allowed_extensions: str = ".pdf,.docx,.txt,.md"
    
    # Project Management Configuration
    max_projects_per_user: int = 1
    max_documents_per_project: int = 5
    max_batch_upload_size: int = 5
    
    # Chunking Configuration
    default_chunk_size: int = 512
    default_chunk_overlap: int = 50
    max_chunk_size: int = 4096
    max_chunk_overlap: int = 200
    
    # Entity Extraction Configuration
    default_confidence_threshold: float = 0.5
    min_confidence_threshold: float = 0.1
    max_confidence_threshold: float = 1.0
    
    # Relationship Extraction Configuration
    relationship_confidence_threshold: float = 0.6
    max_relationships_per_extraction: int = 100
    relationship_extraction_timeout: int = 120
    
    # Embedding Generation Configuration
    embedding_batch_size: int = 100
    embedding_similarity_threshold: float = 0.7
    embedding_search_limit: int = 50
    embedding_generation_timeout: int = 30
    embedding_dimension: int = 3072
    
    # Logging Configuration
    log_level: str = "INFO"
    log_file: str = "./logs/app.log"
    
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()


def setup_pydantic_ai_environment() -> None:
    """Set up environment variables for PydanticAI."""
    settings = get_settings()
    
    # Set OpenAI environment variables for PydanticAI
    os.environ["OPENAI_API_KEY"] = settings.openai_api_key
    os.environ["OPENAI_BASE_URL"] = settings.openai_base_url


def configure_logfire() -> None:
    """Configure Logfire for observability."""
    settings = get_settings()
    
    logfire.configure(
        token=settings.logfire_token,
        service_name="light-rag",
        environment="development" if settings.debug else "production",
    )
    
    # Instrument PydanticAI for automatic observability
    logfire.instrument_pydantic_ai()
    
    # FastAPI instrumentation will be done when app is created
    
    # Instrument asyncpg for database observability
    try:
        logfire.instrument_asyncpg()
    except ImportError:
        pass


def get_openai_client() -> OpenAI:
    """Get OpenAI client configured for OpenRouter."""
    settings = get_settings()
    
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=settings.openrouter_api_key,
    )


def get_openrouter_headers() -> dict[str, str]:
    """Get OpenRouter headers for API requests."""
    return {
        "HTTP-Referer": "https://github.com/svseas/light-rag",
        "X-Title": "LightRAG Demo",
    }


class ModelConfig(BaseModel):
    """Configuration for AI models."""
    
    model_name: str
    client: OpenAI
    headers: dict[str, str]
    temperature: float = 0.7
    max_tokens: Optional[int] = 4096
    
    class Config:
        arbitrary_types_allowed = True


def get_model_config(model_name: Optional[str] = None) -> ModelConfig:
    """Get model configuration for OpenRouter."""
    settings = get_settings()
    model_name = model_name or settings.default_model
    
    return ModelConfig(
        model_name=model_name,
        client=get_openai_client(),
        headers=get_openrouter_headers(),
        temperature=0.7,
        max_tokens=4096,
    )


def setup_directories() -> None:
    """Create necessary directories for the application."""
    settings = get_settings()
    
    # Create upload directory
    os.makedirs(settings.upload_path, exist_ok=True)
    
    # Create logs directory
    os.makedirs(os.path.dirname(settings.log_file), exist_ok=True)