"""
Machine Learning module for semantic search with embeddings.
"""
from app.ml.embedding_service import EmbeddingService
from app.ml.embedding_db import EmbeddingDatabase
from app.ml.model_registry import model_registry
from app.ml.text_preprocessor import TextPreprocessor

__all__ = ["EmbeddingService", "EmbeddingDatabase", "model_registry", "TextPreprocessor"]
