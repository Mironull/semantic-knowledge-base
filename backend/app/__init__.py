"""
Document Store API application package.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes import documents, health


def create_app() -> FastAPI:
    """
    Application factory for creating FastAPI instance.

    Returns:
        FastAPI: Configured FastAPI application
    """
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.VERSION,
        description=settings.DESCRIPTION,
        contact=settings.API_CONTACT,
        license_info=settings.API_LICENSE,
        openapi_tags=[
            {
                "name": "documents",
                "description": "Document management operations: upload, download, search, and preview documents"
            },
            {
                "name": "health",
                "description": "Health check and status endpoints"
            }
        ]
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(documents.router, tags=["documents"])
    app.include_router(health.router, tags=["health"])

    return app
