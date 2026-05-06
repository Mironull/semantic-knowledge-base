"""
Document management API routes.
"""
from datetime import datetime
from typing import List
from uuid import uuid4

from fastapi import APIRouter, File, UploadFile, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.core.config import settings
from app.models import DocumentMetadata, DocumentMetadataWithSize, DocumentSearchResult
from app.services import DatabaseManager, DocumentParserService
from app.ml import EmbeddingService, EmbeddingDatabase, cross_encoder_reranker


# Create router
router = APIRouter()

# Initialize services (singleton pattern)
db_manager = DatabaseManager()
parser_service = DocumentParserService()
embedding_service = EmbeddingService(
    model_name=settings.ML_MODEL_NAME,
    device=settings.ML_DEVICE,
)
embedding_db = EmbeddingDatabase(db_file=settings.EMBEDDINGS_DB_FILE)

if settings.ML_RERANKER_ENABLED:
    cross_encoder_reranker.load(
        model_name=settings.ML_RERANKER_MODEL_NAME,
        device=settings.ML_DEVICE,
    )


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

    # Split into chunks, embed, and store if ML service is available
    if embedding_service.is_available():
        try:
            parsed_data = parser_service.parse_document(
                data=content,
                filename=file.filename,
                content_type=file.content_type
            )
            text_content = parsed_data.get("content", "")

            if text_content and isinstance(text_content, str):
                chunks = embedding_service.split_into_chunks(
                    text_content,
                    chunk_size=settings.ML_CHUNK_SIZE,
                    chunk_overlap=settings.ML_CHUNK_OVERLAP,
                )
                if chunks:
                    embeddings = embedding_service.generate_embeddings_batch(chunks)
                    if embeddings is not None:
                        embedding_db.store_chunks(doc_id, chunks, embeddings)
                        print(f"Stored {len(chunks)} chunks for document {doc_id}")
        except Exception as e:
            print(f"Warning: Failed to generate embeddings for {file.filename}: {e}")

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
    # Try chunk-level semantic search if ML service is available
    if embedding_service.is_available() and embedding_db.get_embedding_count() > 0:
        try:
            query_embedding = embedding_service.generate_embedding(name)

            if query_embedding is not None:
                doc_ids, chunk_indices, chunk_texts, all_embeddings = embedding_db.get_all_embeddings()

                if len(doc_ids) > 0:
                    similarities = embedding_service.compute_similarity(query_embedding, all_embeddings)

                    # Keep best-scoring chunk per document
                    best_per_doc: dict = {}
                    for doc_id, chunk_idx, chunk_text, score in zip(
                        doc_ids, chunk_indices, chunk_texts, similarities.tolist()
                    ):
                        if doc_id not in best_per_doc or score > best_per_doc[doc_id]["score"]:
                            best_per_doc[doc_id] = {
                                "score": score,
                                "chunk_text": chunk_text,
                                "chunk_index": chunk_idx,
                            }

                    # Stage 1: bi-encoder — take ML_RERANK_CANDIDATES for reranker
                    candidate_count = (
                        settings.ML_RERANK_CANDIDATES
                        if settings.ML_RERANKER_ENABLED and cross_encoder_reranker.is_available()
                        else settings.ML_TOP_K
                    )
                    candidates = sorted(
                        best_per_doc.items(),
                        key=lambda x: x[1]["score"],
                        reverse=True,
                    )[:candidate_count]

                    # Stage 2: cross-encoder rerank (if enabled)
                    if settings.ML_RERANKER_ENABLED and cross_encoder_reranker.is_available():
                        candidates = cross_encoder_reranker.rerank(
                            query=name,
                            candidates=candidates,
                            top_k=settings.ML_TOP_K,
                        )
                    else:
                        candidates = candidates[:settings.ML_TOP_K]

                    results = []
                    for doc_id, best in candidates:
                        metadata = db_manager.get_document_metadata(doc_id)
                        if metadata:
                            results.append(DocumentSearchResult(
                                id=metadata.id,
                                filename=metadata.filename,
                                content_type=metadata.content_type,
                                upload_date=metadata.upload_date,
                                similarity_score=best["score"],
                                chunk_text=best["chunk_text"],
                                chunk_index=best["chunk_index"],
                            ))

                    stage = "bi-encoder + cross-encoder rerank" if cross_encoder_reranker.is_available() else "bi-encoder"
                    print(f"Search ({stage}) returned {len(results)} results")
                    return results
        except Exception as e:
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


@router.delete(
    "/documents/{doc_id}",
    summary="Delete Document",
    description="Delete a document and its embedding by ID.",
    responses={
        200: {"description": "Document deleted successfully"},
        404: {"description": "Document not found"}
    }
)
async def delete_document(doc_id: str):
    """Delete a document and its associated embedding."""
    deleted = db_manager.delete_document(doc_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")
    embedding_db.delete_embedding(doc_id)
    return {"message": "Document deleted successfully"}


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
