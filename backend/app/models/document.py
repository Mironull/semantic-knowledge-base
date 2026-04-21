"""
Document-related Pydantic models.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class DocumentMetadata(BaseModel):
    """Basic document metadata."""
    id: str
    filename: str
    content_type: str
    upload_date: datetime


class DocumentMetadataWithSize(BaseModel):
    """Document metadata including file size."""
    id: str
    filename: str
    content_type: str
    upload_date: datetime
    size: int  # size in bytes


class PreviewResponse(BaseModel):
    """Response model for document preview."""
    content: str
    type: str  # "text", "unsupported", "error"
    content_type: str
    size: Optional[int] = None
    pages: Optional[int] = None
