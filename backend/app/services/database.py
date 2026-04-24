"""
Database manager for document storage operations.
"""
import sqlite3
from datetime import datetime
from typing import List, Optional, Tuple
from contextlib import contextmanager

from app.models import DocumentMetadata, DocumentMetadataWithSize
from app.core.config import settings


class DatabaseManager:
    """Manages SQLite database operations for document storage."""

    def __init__(self, db_file: Optional[str] = None):
        """
        Initialize database manager.

        Args:
            db_file: Path to SQLite database file (defaults to settings.DB_FILE)
        """
        self.db_file = db_file or settings.DB_FILE
        self._init_db()

    @contextmanager
    def _get_connection(self):
        """
        Context manager for database connections.

        Yields:
            sqlite3.Connection: Database connection with Row factory
        """
        conn = sqlite3.connect(self.db_file, detect_types=sqlite3.PARSE_DECLTYPES)
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
        """Create the documents table if it doesn't exist."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    filename TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    data BLOB NOT NULL,
                    upload_date TIMESTAMP NOT NULL
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_filename ON documents(filename)")

    def insert_document(
        self,
        doc_id: str,
        filename: str,
        content_type: str,
        data: bytes,
        upload_date: datetime
    ) -> DocumentMetadata:
        """
        Insert a new document into the database.

        Args:
            doc_id: Unique document identifier
            filename: Original filename
            content_type: MIME type
            data: File binary data
            upload_date: Upload timestamp

        Returns:
            DocumentMetadata: Metadata of inserted document
        """
        with self._get_connection() as conn:
            conn.execute(
                "INSERT INTO documents (id, filename, content_type, data, upload_date) VALUES (?, ?, ?, ?, ?)",
                (doc_id, filename, content_type, data, upload_date)
            )

        return DocumentMetadata(
            id=doc_id,
            filename=filename,
            content_type=content_type,
            upload_date=upload_date
        )

    def get_document_data(self, doc_id: str) -> Optional[Tuple[str, str, bytes]]:
        """
        Retrieve document data by ID.

        Args:
            doc_id: Document identifier

        Returns:
            Tuple of (filename, content_type, data) or None if not found
        """
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT filename, content_type, data FROM documents WHERE id = ?",
                (doc_id,)
            ).fetchone()

            if row:
                return (row["filename"], row["content_type"], row["data"])
            return None

    def get_document_metadata(self, doc_id: str) -> Optional[DocumentMetadata]:
        """
        Retrieve document metadata by ID (without file data).

        Args:
            doc_id: Document identifier

        Returns:
            DocumentMetadata or None if not found
        """
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT id, filename, content_type, upload_date FROM documents WHERE id = ?",
                (doc_id,)
            ).fetchone()

            if row:
                return DocumentMetadata(
                    id=row["id"],
                    filename=row["filename"],
                    content_type=row["content_type"],
                    upload_date=self._parse_datetime(row["upload_date"])
                )
            return None

    def search_documents(self, name: str) -> List[DocumentMetadata]:
        """
        Search documents by filename (case-insensitive partial match).

        Args:
            name: Search query string

        Returns:
            List of matching document metadata
        """
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT id, filename, content_type, upload_date FROM documents WHERE filename LIKE ?",
                (f"%{name}%",)
            ).fetchall()

        return [
            DocumentMetadata(
                id=row["id"],
                filename=row["filename"],
                content_type=row["content_type"],
                upload_date=self._parse_datetime(row["upload_date"])
            )
            for row in rows
        ]

    def get_all_documents(self) -> List[DocumentMetadataWithSize]:
        """
        Get all documents with metadata including file size.

        Returns:
            List of all documents with size information
        """
        with self._get_connection() as conn:
            rows = conn.execute(
                "SELECT id, filename, content_type, upload_date, length(data) as size "
                "FROM documents ORDER BY upload_date DESC"
            ).fetchall()

        return [
            DocumentMetadataWithSize(
                id=row["id"],
                filename=row["filename"],
                content_type=row["content_type"],
                upload_date=self._parse_datetime(row["upload_date"]),
                size=row["size"]
            )
            for row in rows
        ]

    @staticmethod
    def _parse_datetime(date_value) -> datetime:
        """
        Parse datetime from various formats.

        Args:
            date_value: Datetime value (string or datetime object)

        Returns:
            datetime: Parsed datetime object
        """
        if isinstance(date_value, str):
            return datetime.fromisoformat(date_value)
        return date_value
