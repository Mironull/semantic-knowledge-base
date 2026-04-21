"""
Health check API routes.
"""
from fastapi import APIRouter

from app.core.config import settings


# Create router
router = APIRouter()


@router.get(
    "/",
    summary="Root Endpoint",
    description="Welcome message and API information.",
    responses={
        200: {
            "description": "API welcome message",
            "content": {
                "application/json": {
                    "example": {
                        "message": "Document Store API is running. Visit /docs for API documentation.",
                        "version": "1.0.0"
                    }
                }
            }
        }
    }
)
async def root():
    """
    Welcome endpoint for the API.

    Returns basic information about the API and a link to the documentation.
    """
    return {
        "message": f"{settings.APP_NAME} is running. Visit /docs for API documentation.",
        "version": settings.VERSION,
        "docs": "/docs"
    }


@router.get(
    "/health",
    summary="Health Check",
    description="Detailed health status of the API service.",
    responses={
        200: {
            "description": "Service health status",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "version": "1.0.0",
                        "app": "Document Store API"
                    }
                }
            }
        }
    }
)
async def health_check():
    """
    Health check endpoint for monitoring.

    Use this endpoint to verify that the API is running and responding correctly.
    Returns the service status, version, and application name.
    """
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "app": settings.APP_NAME
    }
