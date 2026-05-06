"""
Application configuration settings.
"""
from typing import List, Dict
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
    EMBEDDINGS_DB_FILE: str = "embeddings.db"

    # CORS configuration
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # ML configuration
    ML_MODEL_NAME: str = "paraphrase-multilingual-mpnet-base-v2"
    ML_DEVICE: str = "cpu"
    ML_CHUNK_SIZE: int = 400
    ML_TOP_K: int = 3

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
