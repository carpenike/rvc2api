"""
Documentation API Router

FastAPI router for documentation search and API schema operations.
This router delegates business logic to the DocsService.

Routes:
- GET /docs/status: Get status of the vector search service
- GET /docs/search: Search RV-C documentation using vector embeddings
- GET /docs/openapi: Get the OpenAPI schema for the API
"""

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request

from backend.core.dependencies import (
    get_docs_service,
    get_feature_manager_from_request,
    get_vector_service,
)

logger = logging.getLogger(__name__)

# Create the router
router = APIRouter(prefix="/api/docs", tags=["documentation"])


def _check_api_docs_feature_enabled(request: Request) -> None:
    """
    Check if the api_docs feature is enabled.

    Raises HTTPException with 404 status if the feature is disabled.
    This allows documentation endpoints to be conditionally available
    based on the api_docs feature flag.
    """
    feature_manager = get_feature_manager_from_request(request)
    if not feature_manager.is_enabled("api_docs"):
        raise HTTPException(
            status_code=404,
            detail="api_docs feature is disabled",
        )


@router.get(
    "/status",
    response_model=dict[str, Any],
    summary="Get documentation search status",
    description="Returns the status of the vector search service and its configuration.",
)
async def get_search_status(
    request: Request,
    vector_service: Annotated[Any, Depends(get_vector_service)] = None,
) -> dict[str, Any]:
    """Get the status of the vector search service."""
    _check_api_docs_feature_enabled(request)
    status = vector_service.get_status()

    return {
        "vector_search": {
            "available": vector_service.is_available(),
            **status,
        }
    }


@router.get(
    "/search",
    response_model=list[dict[str, Any]],
    summary="Search RV-C documentation",
    description="Search the RV-C documentation using vector-based semantic search.",
)
async def search_documentation(
    request: Request,
    query: str = Query(..., description="Search query string"),
    k: int = Query(3, description="Number of results to return", ge=1, le=10),
    vector_service: Annotated[Any, Depends(get_vector_service)] = None,
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
    _check_api_docs_feature_enabled(request)

    try:
        if not vector_service.is_available():
            status = vector_service.get_status()
            error_detail = status.get("error", "Unknown error")
            logger.error(f"Vector search service is not available: {error_detail}")
            raise HTTPException(
                status_code=503,
                detail=(
                    f"Vector search service is not available: {error_detail}. "
                    "Run 'python scripts/setup_faiss.py --setup' to configure the search feature."
                ),
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


@router.get(
    "/openapi",
    response_model=dict[str, Any],
    summary="Get OpenAPI schema",
    description="Returns the complete OpenAPI schema for the API.",
)
async def get_openapi_schema(
    request: Request,
    docs_service: Annotated[Any, Depends(get_docs_service)] = None,
) -> dict[str, Any]:
    """Get the complete OpenAPI schema for the API."""
    _check_api_docs_feature_enabled(request)

    try:
        schema = await docs_service.get_openapi_schema()
        return schema
    except Exception as e:
        logger.error(f"Error generating OpenAPI schema: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error generating OpenAPI schema",
        ) from e
