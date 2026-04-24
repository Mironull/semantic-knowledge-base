"""
Model registry for managing embedding model lifecycle.
"""
import time
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None


@dataclass
class ModelMetadata:
    """Stores metadata about the loaded model."""
    name: str
    dimension: int
    max_seq_length: int
    device: str
    load_time_seconds: float
    total_parameters: int = 0


@dataclass
class ModelRegistry:
    """
    Manages lifecycle and access to embedding models.

    Handles model loading, warm-up, and provides a clean interface
    for obtaining embeddings from the underlying transformer.
    """
    _model: Optional[object] = field(default=None, init=False, repr=False)
    _metadata: Optional[ModelMetadata] = field(default=None, init=False)
    _is_ready: bool = field(default=False, init=False)

    def load(
        self,
        model_name: str = 'all-MiniLM-L6-v2',
        device: str = 'cpu',
        cache_dir: Optional[str] = None
    ) -> None:
        """Load the embedding model into memory and perform warm-up."""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            print("WARNING: sentence-transformers not available. ML features disabled.")
            return

        print(f"Loading model '{model_name}' on device '{device}'...")

        start = time.perf_counter()
        self._model = SentenceTransformer(
            model_name,
            cache_folder=cache_dir,
            device=device,
        )
        load_time = time.perf_counter() - start

        total_params = sum(p.numel() for p in self._model.parameters())

        # Get embedding dimension
        test_embedding = self._model.encode(["test"])
        embedding_dim = test_embedding.shape[1]

        self._metadata = ModelMetadata(
            name=model_name,
            dimension=embedding_dim,
            max_seq_length=self._model.max_seq_length,
            device=device,
            load_time_seconds=round(load_time, 3),
            total_parameters=total_params,
        )

        print(
            f"Model loaded in {load_time:.2f}s | dim={embedding_dim} | "
            f"params={total_params:,} | max_seq={self._model.max_seq_length}"
        )

        self._warm_up()
        self._is_ready = True

    def _warm_up(self) -> None:
        """Run a warm-up inference to initialize CUDA kernels / optimize graph."""
        print("Running warm-up inference...")
        warmup_texts = [
            "warm-up sentence for model initialization",
            "second warm-up sentence to stabilize latency",
        ]
        self._model.encode(warmup_texts, show_progress_bar=False)
        print("Warm-up complete.")

    def encode(
        self,
        texts,
        normalize: bool = True,
        batch_size: int = 32,
    ) -> np.ndarray:
        """
        Encode text(s) into dense vector embeddings.

        Args:
            texts: Single text or list of texts to encode.
            normalize: Whether to L2-normalize the output vectors.
            batch_size: Batch size for encoding multiple texts.

        Returns:
            Numpy array of shape (n, dim) for multiple texts or (dim,) for single.
        """
        if not self._is_ready:
            raise RuntimeError("Model is not loaded. Call load() first.")

        single_input = isinstance(texts, str)
        if single_input:
            texts = [texts]

        embeddings = self._model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=normalize,
            show_progress_bar=False,
            convert_to_numpy=True,
        )

        if single_input:
            return embeddings[0]
        return embeddings

    def unload(self) -> None:
        """Release model from memory."""
        if self._model is not None:
            print(f"Unloading model '{self._metadata.name}'...")
            del self._model
            self._model = None
            self._is_ready = False

    @property
    def metadata(self) -> Optional[ModelMetadata]:
        return self._metadata

    @property
    def is_ready(self) -> bool:
        return self._is_ready


# Singleton instance
model_registry = ModelRegistry()
