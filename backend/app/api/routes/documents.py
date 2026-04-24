"""
Document management API routes.
"""
from datetime import datetime
from typing import List
from uuid import uuid4

from fastapi import APIRouter, File, UploadFile, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.models import DocumentMetadata, DocumentMetadataWithSize, DocumentSearchResult
from app.services import DatabaseManager, DocumentParserService
from app.ml import EmbeddingService, EmbeddingDatabase


# Create router
router = APIRouter()

# Initialize services (singleton pattern)
db_manager = DatabaseManager()
parser_service = DocumentParserService()
embedding_service = EmbeddingService()
embedding_db = EmbeddingDatabase()


@router.post(
    "/upload",
    response_model=DocumentMetadata,
    summary="Upload Document",
    description="Upload a document to the storage. Supports multiple formats including PDF, DOCX, TXT, JSON, and more.",
    responses={
        200: {
            "description": "Document uploaded successfully",
            "content": {
                "application/json": {
                    "example": {
                        "id": "123e4567-e89b-12d3-a456-426614174000",
                        "filename": "example.pdf",
                        "content_type": "application/pdf",
                        "upload_date": "2025-04-21T12:00:00"
                    }
                }
            }
        }
    }
)
async def upload_document(
    file: UploadFile = File(..., description="The document file to upload")
):
    """
    Upload a document and store it in SQLite database.

    The document will be stored with a unique UUID identifier and can be
    retrieved, searched, or previewed later using the document ID.

    **Machine Learning Integration:**
    - Automatically generates embeddings for semantic search
    - Supports multilingual content (including Russian)
    - Embeddings stored in separate database

    **Supported formats:**
    - PDF (application/pdf)
    - Word documents (application/vnd.openxmlformats-officedocument.wordprocessingml.document)
    - Text files (text/plain, text/html, text/csv)
    - JSON files (application/json)
    - XML files (application/xml)
    """
    content = await file.read()
    doc_id = str(uuid4())
    now = datetime.utcnow()

    # Store document in main database
    metadata = db_manager.insert_document(
        doc_id=doc_id,
        filename=file.filename,
        content_type=file.content_type,
        data=content,
        upload_date=now
    )

    # Generate and store embedding if ML service is available
    if embedding_service.is_available():
        try:
            # Extract text content from document
            parsed_data = parser_service.parse_document(
                data=content,
                filename=file.filename,
                content_type=file.content_type
            )

            # Get text content (handle different response types)
            text_content = parsed_data.get("content", "")

            # Generate embedding if we have text content
            if text_content and isinstance(text_content, str):
                embedding = embedding_service.generate_embedding(text_content)
                if embedding is not None:
                    embedding_db.store_embedding(doc_id, embedding)
                    print(f"Generated and stored embedding for document {doc_id}")
        except Exception as e:
            # Log error but don't fail the upload
            print(f"Warning: Failed to generate embedding for {file.filename}: {e}")

    return metadata


@router.get(
    "/download/{doc_id}",
    summary="Download Document",
    description="Download a document by its unique ID. Returns the original file with appropriate content type.",
    responses={
        200: {
            "description": "Document file",
            "content": {
                "application/octet-stream": {
                    "example": "Binary file content"
                }
            }
        },
        404: {
            "description": "Document not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Document not found"}
                }
            }
        }
    }
)
async def download_document(
    doc_id: str
):
    """
    Download a document by its unique identifier.

    The document will be returned with its original filename and content type,
    allowing the browser to handle it appropriately (download or display).
    """
    result = db_manager.get_document_data(doc_id)

    if not result:
        raise HTTPException(status_code=404, detail="Document not found")

    filename, content_type, data = result

    return StreamingResponse(
        iter([data]),
        media_type=content_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get(
    "/search",
    response_model=List[DocumentSearchResult],
    summary="Search Documents",
    description="Search for documents using semantic search with similarity scores.",
    responses={
        200: {
            "description": "List of matching documents with similarity scores",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "filename": "report.pdf",
                            "content_type": "application/pdf",
                            "upload_date": "2025-04-21T12:00:00",
                            "similarity_score": 0.8542
                        }
                    ]
                }
            }
        }
    }
)
async def search_documents(
    name: str = Query(
        ...,
        min_length=1,
        description="Search query for semantic or filename search",
        example="machine learning algorithms"
    )
):
    """
    Search for documents using semantic search and filename matching.

    **Search Methods:**
    1. **Semantic Search** (Primary): Uses machine learning to find documents
       based on meaning and context, not just keywords. Works with multilingual
       content including Russian.
    2. **Filename Search** (Fallback): If ML is not available, performs
       case-insensitive partial match on document filenames.

    **Examples:**
    - "машинное обучение" - finds documents about machine learning in Russian
    - "neural networks" - finds related documents even without exact phrase match
    - "report" - finds all documents with "report" in filename

    Returns documents sorted by relevance (similarity score for semantic search).
    """
    # Try semantic search if ML service is available
    if embedding_service.is_available() and embedding_db.get_embedding_count() > 0:
        try:
            # Generate embedding for query
            query_embedding = embedding_service.generate_embedding(name)

            if query_embedding is not None:
                # Get all document embeddings
                doc_ids, doc_embeddings = embedding_db.get_all_embeddings()

                if len(doc_ids) > 0:
                    # Find most similar documents
                    similar_docs = embedding_service.find_most_similar(
                        query_embedding=query_embedding,
                        doc_embeddings=doc_embeddings,
                        doc_ids=doc_ids,
                        top_k=20  # Return top 20 most similar documents
                    )

                    # Retrieve metadata for similar documents with similarity scores
                    results = []
                    for doc_id, similarity_score in similar_docs:
                        metadata = db_manager.get_document_metadata(doc_id)
                        if metadata:
                            # Convert to search result with similarity score
                            search_result = DocumentSearchResult(
                                id=metadata.id,
                                filename=metadata.filename,
                                content_type=metadata.content_type,
                                upload_date=metadata.upload_date,
                                similarity_score=round(similarity_score, 4)
                            )
                            results.append(search_result)

                    print(f"Semantic search returned {len(results)} results")
                    return results
        except Exception as e:
            # Log error and fall back to filename search
            print(f"Warning: Semantic search failed, falling back to filename search: {e}")

    # Fallback to filename search (no similarity scores)
    print("Using filename search")
    filename_results = db_manager.search_documents(name)

    # Convert to search results without similarity scores
    return [
        DocumentSearchResult(
            id=doc.id,
            filename=doc.filename,
            content_type=doc.content_type,
            upload_date=doc.upload_date,
            similarity_score=None
        )
        for doc in filename_results
    ]


@router.get(
    "/documents",
    response_model=List[DocumentMetadataWithSize],
    summary="List All Documents",
    description="Retrieve all documents from the database with metadata including file size.",
    responses={
        200: {
            "description": "List of all documents",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": "123e4567-e89b-12d3-a456-426614174000",
                            "filename": "report.pdf",
                            "content_type": "application/pdf",
                            "upload_date": "2025-04-21T12:00:00",
                            "size": 102400
                        }
                    ]
                }
            }
        }
    }
)
async def list_all_documents():
    """
    List all documents in the database.

    Returns all documents ordered by upload date (newest first) with metadata
    including filename, content type, upload date, and file size in bytes.
    """
    return db_manager.get_all_documents()


@router.get(
    "/preview/{doc_id}",
    summary="Preview Document",
    description="Extract and preview text content from documents. Supports TXT, JSON, PDF, and DOCX formats.",
    responses={
        200: {
            "description": "Document preview content",
            "content": {
                "application/json": {
                    "examples": {
                        "text_file": {
                            "summary": "Text file preview",
                            "value": {
                                "content": "This is the text content...",
                                "type": "text",
                                "content_type": "text/plain"
                            }
                        },
                        "pdf_file": {
                            "summary": "PDF file preview",
                            "value": {
                                "content": "=== Страница 1 ===\nExtracted text...",
                                "type": "text",
                                "content_type": "application/pdf",
                                "pages": 5
                            }
                        },
                        "unsupported": {
                            "summary": "Unsupported format",
                            "value": {
                                "content": "Предпросмотр недоступен для формата image/png",
                                "type": "unsupported",
                                "content_type": "image/png",
                                "size": 204800
                            }
                        }
                    }
                }
            }
        },
        404: {
            "description": "Document not found",
            "content": {
                "application/json": {
                    "example": {"detail": "Document not found"}
                }
            }
        }
    }
)
async def preview_document(doc_id: str):
    """
    Preview document content by extracting text.

    Extracts and returns text content from supported document formats:
    - **Text files**: Returns raw text content
    - **PDF files**: Extracts text from all pages with page markers
    - **DOCX files**: Extracts text from paragraphs and tables
    - **JSON/XML**: Returns formatted text content

    For unsupported formats (images, etc.), returns an informational message.
    """
    result = db_manager.get_document_data(doc_id)

    if not result:
        raise HTTPException(status_code=404, detail="Document not found")

    filename, content_type, data = result

    # Parse document using appropriate parser
    preview_data = parser_service.parse_document(
        data=data,
        filename=filename,
        content_type=content_type
    )

    return preview_data
