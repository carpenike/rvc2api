"""
Router for RV-C documentation search API endpoints.

This module provides API endpoints for searching RV-C specification documentation
using vector embeddings and semantic search.
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from core_daemon.services.vector_service import VectorService, get_vector_service

# Create a logger for this module
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/docs",
    tags=["documentation"],
)


@router.get("/search")
async def search_documentation(
    query: str = Query(..., description="Search query string"),
    k: int = Query(3, description="Number of results to return", ge=1, le=10),
    # Dependency injection for vector_service
    vector_service: VectorService = None,
) -> list[dict[str, Any]]:
    """
    Search the RV-C documentation using vector-based semantic search.

    Args:
        query: Natural language search query
        k: Number of results to return (between 1 and 10)
        vector_service: Vector service dependency

    Returns:
        List of search results with content and metadata

    Raises:
        HTTPException: If search fails or service is unavailable
    """
    if vector_service is None:
        from fastapi import Depends

        vector_service = Depends(get_vector_service)
    try:
        if not vector_service.is_available():
            logger.error("Vector search service is not available")
            raise HTTPException(
                status_code=503,
                detail="Vector search service is not available. Check server logs for details.",
            )

        results = vector_service.similarity_search(query, k=k)
        return results

    except RuntimeError as e:
        logger.error(f"Error in vector search: {e}")
        raise HTTPException(
            status_code=503,
            detail="Vector search service encountered an error. Check server logs for details.",
        ) from e
    except Exception as e:
        logger.error(f"Unexpected error in vector search: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during the search.",
        ) from e
