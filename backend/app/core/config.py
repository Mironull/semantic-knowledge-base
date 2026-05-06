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

    # ML — bi-encoder
    ML_MODEL_NAME: str = "paraphrase-multilingual-mpnet-base-v2"
    ML_DEVICE: str = "cpu"
    ML_CHUNK_SIZE: int = 800
    ML_CHUNK_OVERLAP: int = 1   # число предложений, переносимых в следующий чанк
    ML_TOP_K: int = 3

    # ML — cross-encoder reranker
    ML_RERANKER_ENABLED: bool = True
    ML_RERANKER_MODEL_NAME: str = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"
    ML_RERANK_CANDIDATES: int = 20  # кандидатов от bi-encoder перед rerank

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
