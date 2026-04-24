"""
Embedding service for generating and managing document embeddings.
"""
import time
from typing import List, Tuple, Optional

import numpy as np

from app.ml.model_registry import model_registry
from app.ml.text_preprocessor import TextPreprocessor


class EmbeddingService:
    """
    High-level service for computing text embeddings.

    Orchestrates preprocessing, batching, and model inference.
    Handles chunked encoding for large batches to prevent OOM.
    """

    def __init__(
        self,
        model_name: str = 'all-MiniLM-L6-v2',
        device: str = 'cpu',
        enable_preprocessing: bool = True
    ):
        """
        Initialize embedding service.

        Args:
            model_name: Name of the sentence transformer model.
                       Default uses multilingual model that supports Russian.
            device: Device to run model on ('cpu' or 'cuda').
            enable_preprocessing: Whether to enable text preprocessing.
        """
        self.model_name = model_name
        self.device = device
        self._preprocessor = TextPreprocessor(enable=enable_preprocessing)
        self._loaded = False

        # Try to load model
        try:
            model_registry.load(model_name=model_name, device=device)
            self._loaded = True
        except Exception as e:
            print(f"WARNING: Failed to load embedding model: {e}")
            print("Embedding features will be disabled.")

    def is_available(self) -> bool:
        """Check if embedding service is available."""
        return self._loaded and model_registry.is_ready

    def generate_embedding(self, text: str, normalize: bool = True) -> Optional[np.ndarray]:
        """
        Generate embedding for a single text.

        Args:
            text: Input text.
            normalize: Whether to L2-normalize the vector.

        Returns:
            Numpy array of embeddings or None if model not available.
        """
        if not self.is_available():
            return None

        if not text or not text.strip():
            return None

        try:
            # Preprocess text
            processed = self._preprocessor.preprocess(text)

            if not processed:
                print("WARNING: Empty text after preprocessing, returning None")
                return None

            # Generate embedding
            start = time.perf_counter()
            vector = model_registry.encode(processed, normalize=normalize)
            elapsed = time.perf_counter() - start

            print(
                f"Encoded single text in {elapsed:.4f}s | "
                f"len={len(processed)} | norm={float(np.linalg.norm(vector)):.4f}"
            )

            return vector

        except Exception as e:
            print(f"Error generating embedding: {e}")
            return None

    def generate_embeddings_batch(
        self,
        texts: List[str],
        normalize: bool = True,
        batch_size: int = 32
    ) -> Optional[np.ndarray]:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of input texts.
            normalize: Whether to L2-normalize vectors.
            batch_size: Batch size for processing.

        Returns:
            Numpy array of embeddings or None if model not available.
        """
        if not self.is_available():
            return None

        if not texts:
            return None

        try:
            # Preprocess texts
            processed = self._preprocessor.preprocess_batch(texts)

            empty_indices = [i for i, t in enumerate(processed) if not t]
            if empty_indices:
                print(
                    f"WARNING: Found {len(empty_indices)} empty texts after preprocessing"
                )

            non_empty_texts = [t for t in processed if t]

            if not non_empty_texts:
                return None

            # Generate embeddings
            start = time.perf_counter()
            vectors = model_registry.encode(
                non_empty_texts,
                normalize=normalize,
                batch_size=batch_size
            )
            elapsed = time.perf_counter() - start

            print(
                f"Encoded batch of {len(texts)} texts in {elapsed:.4f}s "
                f"({len(non_empty_texts) / elapsed:.1f} texts/sec)"
            )

            return vectors

        except Exception as e:
            print(f"Error generating embeddings: {e}")
            return None

    def compute_similarity(
        self,
        query_embedding: np.ndarray,
        doc_embeddings: np.ndarray
    ) -> np.ndarray:
        """
        Compute cosine similarity between query and document embeddings.

        Args:
            query_embedding: Query embedding vector.
            doc_embeddings: Matrix of document embeddings.

        Returns:
            Array of similarity scores.
        """
        # Normalize vectors
        query_norm = query_embedding / np.linalg.norm(query_embedding)
        doc_norms = doc_embeddings / np.linalg.norm(doc_embeddings, axis=1, keepdims=True)

        # Compute cosine similarity
        similarities = np.dot(doc_norms, query_norm)

        return similarities

    def find_most_similar(
        self,
        query_embedding: np.ndarray,
        doc_embeddings: np.ndarray,
        doc_ids: List[str],
        top_k: int = 10
    ) -> List[Tuple[str, float]]:
        """
        Find most similar documents to query.

        Args:
            query_embedding: Query embedding vector.
            doc_embeddings: Matrix of document embeddings.
            doc_ids: List of document IDs corresponding to embeddings.
            top_k: Number of top results to return.

        Returns:
            List of (doc_id, similarity_score) tuples, sorted by similarity.
        """
        if len(doc_embeddings) == 0:
            return []

        # Compute similarities
        similarities = self.compute_similarity(query_embedding, doc_embeddings)

        # Get top k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]

        # Return (doc_id, score) pairs
        results = [(doc_ids[idx], float(similarities[idx])) for idx in top_indices]

        return results

    def get_embedding_dimension(self) -> Optional[int]:
        """Get the dimension of embeddings produced by this model."""
        if model_registry.metadata:
            return model_registry.metadata.dimension
        return None
