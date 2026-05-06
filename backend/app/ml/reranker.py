"""
Cross-encoder reranker for improving bi-encoder search results.
"""
import math
import time
from typing import List, Tuple, Dict, Optional

try:
    from sentence_transformers import CrossEncoder
    CROSS_ENCODER_AVAILABLE = True
except ImportError:
    CROSS_ENCODER_AVAILABLE = False
    CrossEncoder = None


class CrossEncoderReranker:
    """
    Reranks bi-encoder candidates using a cross-encoder model.

    Cross-encoder sees (query, chunk) jointly through self-attention,
    producing more accurate relevance scores than independent bi-encoder vectors.
    Intended for two-stage retrieval: bi-encoder narrows candidates fast,
    cross-encoder re-scores the shortlist precisely.
    """

    def __init__(self) -> None:
        self._model: Optional[object] = None
        self._model_name: Optional[str] = None
        self._loaded: bool = False

    def load(self, model_name: str, device: str = "cpu") -> None:
        """Load the cross-encoder model."""
        if not CROSS_ENCODER_AVAILABLE:
            print("WARNING: sentence-transformers not available, reranking disabled.")
            return

        print(f"Loading cross-encoder '{model_name}' on device '{device}'...")
        start = time.perf_counter()
        self._model = CrossEncoder(model_name, device=device)
        self._model_name = model_name
        self._loaded = True
        elapsed = time.perf_counter() - start
        print(f"Cross-encoder loaded in {elapsed:.2f}s")

    def is_available(self) -> bool:
        return self._loaded and self._model is not None

    def rerank(
        self,
        query: str,
        candidates: List[Tuple[str, Dict]],
        top_k: int,
    ) -> List[Tuple[str, Dict]]:
        """
        Rerank bi-encoder candidates and return top_k results.

        Args:
            query: Search query string.
            candidates: List of (doc_id, info) where info has keys
                        'chunk_text', 'chunk_index', 'score'.
            top_k: Number of results to return after reranking.

        Returns:
            Top-k candidates sorted by cross-encoder score descending.
            The 'score' field in each info dict is replaced with the
            sigmoid-normalised cross-encoder score.
        """
        if not self.is_available() or not candidates:
            return candidates[:top_k]

        pairs = [(query, info["chunk_text"]) for _, info in candidates]

        start = time.perf_counter()
        raw_scores = self._model.predict(pairs)
        elapsed = time.perf_counter() - start
        print(
            f"Cross-encoder reranked {len(candidates)} candidates "
            f"in {elapsed:.4f}s"
        )

        reranked = sorted(
            zip(candidates, raw_scores),
            key=lambda x: x[1],
            reverse=True,
        )

        results = []
        for (doc_id, info), raw_score in reranked[:top_k]:
            updated = dict(info)
            updated["score"] = round(_sigmoid(float(raw_score)), 4)
            results.append((doc_id, updated))

        return results


def _sigmoid(x: float) -> float:
    """Normalise a raw logit to [0, 1]."""
    return 1.0 / (1.0 + math.exp(-x))


# Singleton instance
cross_encoder_reranker = CrossEncoderReranker()
