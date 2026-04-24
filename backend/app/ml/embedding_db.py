"""
Separate database for storing document embeddings.
"""
import sqlite3
import numpy as np
from typing import List, Optional, Tuple
from contextlib import contextmanager


class EmbeddingDatabase:
    """Manages SQLite database for document embeddings."""

    def __init__(self, db_file: Optional[str] = None):
        """
        Initialize embedding database manager.

        Args:
            db_file: Path to embeddings database file
        """
        self.db_file = db_file or "embeddings.db"
        self._init_db()

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self) -> None:
        """Create the embeddings table if it doesn't exist."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS embeddings (
                    doc_id TEXT PRIMARY KEY,
                    embedding BLOB NOT NULL,
                    embedding_dim INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_doc_id ON embeddings(doc_id)")

    def store_embedding(self, doc_id: str, embedding: np.ndarray) -> None:
        """
        Store embedding for a document.

        Args:
            doc_id: Document ID
            embedding: Embedding vector as numpy array
        """
        with self._get_connection() as conn:
            # Convert numpy array to bytes
            embedding_bytes = embedding.tobytes()
            embedding_dim = len(embedding)

            # Insert or replace
            conn.execute(
                """
                INSERT OR REPLACE INTO embeddings (doc_id, embedding, embedding_dim)
                VALUES (?, ?, ?)
                """,
                (doc_id, embedding_bytes, embedding_dim)
            )

    def get_embedding(self, doc_id: str) -> Optional[np.ndarray]:
        """
        Retrieve embedding for a document.

        Args:
            doc_id: Document ID

        Returns:
            Embedding vector as numpy array or None if not found
        """
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT embedding, embedding_dim FROM embeddings WHERE doc_id = ?",
                (doc_id,)
            ).fetchone()

            if not row:
                return None

            # Convert bytes back to numpy array
            embedding = np.frombuffer(row["embedding"], dtype=np.float32)

            return embedding

    def get_all_embeddings(self) -> Tuple[List[str], np.ndarray]:
        """
        Retrieve all embeddings.

        Returns:
            Tuple of (doc_ids, embeddings_matrix)
        """
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT doc_id, embedding, embedding_dim FROM embeddings"
            ).fetchall()

            if not rows:
                return [], np.array([])

            doc_ids = []
            embeddings = []

            for row in rows:
                doc_ids.append(row["doc_id"])
                embedding = np.frombuffer(row["embedding"], dtype=np.float32)
                embeddings.append(embedding)

            embeddings_matrix = np.vstack(embeddings)

            return doc_ids, embeddings_matrix

    def delete_embedding(self, doc_id: str) -> None:
        """
        Delete embedding for a document.

        Args:
            doc_id: Document ID
        """
        with self._get_connection() as conn:
            conn.execute("DELETE FROM embeddings WHERE doc_id = ?", (doc_id,))

    def embedding_exists(self, doc_id: str) -> bool:
        """
        Check if embedding exists for a document.

        Args:
            doc_id: Document ID

        Returns:
            True if embedding exists, False otherwise
        """
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT COUNT(*) as count FROM embeddings WHERE doc_id = ?",
                (doc_id,)
            ).fetchone()

            return row["count"] > 0

    def get_embedding_count(self) -> int:
        """Get total number of stored embeddings."""
        with self._get_connection() as conn:
            row = conn.execute("SELECT COUNT(*) as count FROM embeddings").fetchone()
            return row["count"]
