"""
Separate database for storing document chunk embeddings.
"""
import sqlite3
import numpy as np
from typing import List, Optional, Tuple
from contextlib import contextmanager


class EmbeddingDatabase:
    """Manages SQLite database for document chunk embeddings."""

    def __init__(self, db_file: Optional[str] = None):
        self.db_file = db_file or "embeddings.db"
        self._init_db()

    @contextmanager
    def _get_connection(self):
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
        with self._get_connection() as conn:
            # Drop old single-embedding table from previous schema
            conn.execute("DROP TABLE IF EXISTS embeddings")
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chunks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    doc_id TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    chunk_text TEXT NOT NULL,
                    embedding BLOB NOT NULL,
                    embedding_dim INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_doc_id ON chunks(doc_id)")

    def store_chunks(self, doc_id: str, chunks: List[str], embeddings: np.ndarray) -> None:
        """
        Store text chunks and their embeddings for a document.

        Args:
            doc_id: Document ID
            chunks: List of chunk texts
            embeddings: 2-D numpy array of shape (n_chunks, dim)
        """
        with self._get_connection() as conn:
            conn.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))
            for i, (chunk_text, embedding) in enumerate(zip(chunks, embeddings)):
                conn.execute(
                    "INSERT INTO chunks (doc_id, chunk_index, chunk_text, embedding, embedding_dim) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (doc_id, i, chunk_text, embedding.tobytes(), len(embedding))
                )

    def get_all_embeddings(self) -> Tuple[List[str], List[int], List[str], np.ndarray]:
        """
        Retrieve all chunk embeddings.

        Returns:
            Tuple of (doc_ids, chunk_indices, chunk_texts, embeddings_matrix)
        """
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT doc_id, chunk_index, chunk_text, embedding FROM chunks"
            ).fetchall()

            if not rows:
                return [], [], [], np.array([])

            doc_ids, chunk_indices, chunk_texts, embeddings = [], [], [], []
            for row in rows:
                doc_ids.append(row["doc_id"])
                chunk_indices.append(row["chunk_index"])
                chunk_texts.append(row["chunk_text"])
                embeddings.append(np.frombuffer(row["embedding"], dtype=np.float32))

            return doc_ids, chunk_indices, chunk_texts, np.vstack(embeddings)

    def delete_embedding(self, doc_id: str) -> None:
        """Delete all chunks for a document."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM chunks WHERE doc_id = ?", (doc_id,))

    def get_embedding_count(self) -> int:
        """Get total number of stored chunks."""
        with self._get_connection() as conn:
            row = conn.execute("SELECT COUNT(*) as count FROM chunks").fetchone()
            return row["count"]
