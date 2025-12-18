"""
Application configuration using Pydantic Settings.
Loads environment variables with validation and type coercion.
"""
from functools import lru_cache
from typing import List, Optional
from pydantic import field_validator, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    All settings have sensible defaults for development.
    Production deployments MUST set sensitive values via environment.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Faceless YouTube Factory"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"
    
    # Database
    database_url: str = "postgresql+asyncpg://youtube_factory:1122qwaszxC@localhost:5432/youtube_factory"
    db_pool_size: int = 20
    db_max_overflow: int = 10

    # CORS
    frontend_url: str = "http://localhost:3000"
    cors_origins: List[str] = ["http://localhost:3000"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    # Groq API
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    groq_max_tokens: int = 4096
    groq_temperature: float = 0.7

    # Google OAuth for YouTube API
    google_client_id: str = ""
    google_client_secret: str = ""
    oauth_redirect_uri: str = "http://localhost:3000/api/youtube/callback"

    # Token Encryption
    token_encryption_key: str = ""

    # File Storage
    static_dir: str = "static"
    max_upload_size_mb: int = 500
    preview_cleanup_minutes: int = 2

    # Rate Limiting
    max_projects_per_hour: int = 10
    max_concurrent_video_jobs: int = 3
    youtube_daily_upload_limit: int = 15

    # Cleanup
    project_retention_days: int = 30

    # Validation
    max_script_prompt_length: int = 5000

    @property
    def async_database_url(self) -> str:
        """Ensure the database URL uses asyncpg driver."""
        url = self.database_url
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

@lru_cache()
def get_settings() -> Settings:
    """
    Get cached application settings.
    
    Uses lru_cache to avoid re-reading environment on every call.
    Clear cache in tests with: get_settings.cache_clear()
    """
    return Settings()

# Export a settings instance
settings = get_settings()