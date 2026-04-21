"""
Application configuration settings.
"""
from typing import List, Dict, Any
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Application metadata
    APP_NAME: str = "Document Store API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Document storage API with search and preview capabilities"

    # API metadata
    API_CONTACT: Dict[str, str] = {
        "name": "API Support",
        "email": "support@example.com"
    }
    API_LICENSE: Dict[str, str] = {
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    }

    # Database configuration
    DB_FILE: str = "docstore.db"

    # CORS configuration
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
