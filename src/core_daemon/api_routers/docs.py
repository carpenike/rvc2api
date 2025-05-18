"""
Router for RV-C documentation search API endpoints.

This module provides API endpoints for searching RV-C specification documentation
using vector embeddings and semantic search.
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query

from core_daemon.services.vector_service import get_vector_service

# Create a logger for this module
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/docs",
    tags=["documentation"],
)


@router.get("/status")
async def get_search_status() -> dict[str, Any]:
    """
    Get the status of the vector search service.

    Returns:
        Dictionary with status information and configuration
    """
    vector_service = get_vector_service()
    status = vector_service.get_status()
    return {
        "vector_search": {
            "available": vector_service.is_available(),
            **status,
        }
    }


@router.get("/search")
async def search_documentation(
    query: str = Query(..., description="Search query string"),
    k: int = Query(3, description="Number of results to return", ge=1, le=10),
) -> list[dict[str, Any]]:
    """
    Search the RV-C documentation using vector-based semantic search.

    Args:
        query: Natural language search query
        k: Number of results to return (between 1 and 10)

    Returns:
        List of search results with content and metadata

    Raises:
        HTTPException: If search fails or service is unavailable
    """
    vector_service = get_vector_service()
    try:
        if not vector_service.is_available():
            status = vector_service.get_status()
            error_detail = status.get("error", "Unknown error")
            logger.error(f"Vector search service is not available: {error_detail}")
            raise HTTPException(
                status_code=503,
                detail=f"Vector search service is not available: {error_detail}. "
                "Run 'python scripts/setup_faiss.py --setup' to configure the search feature.",
            )

        results = vector_service.similarity_search(query, k=k)
        return results

    except RuntimeError as e:
        logger.error(f"Error in vector search: {e}")
        raise HTTPException(
            status_code=503,
            detail=str(e),
        ) from e
    except Exception as e:
        logger.error(f"Unexpected error in vector search: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during the search.",
        ) from e
