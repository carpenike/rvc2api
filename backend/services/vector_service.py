"""
Vector service for the CoachIQ backend.

This is a simplified version that provides a consistent interface for vector search
functionality. Currently acts as a placeholder until full vector search is implemented.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class VectorService:
    """
    Service for managing vector embeddings and semantic search.

    This is a simplified implementation that provides status information
    and error handling for vector search functionality.
    """

    def __init__(self, index_path: str | None = None) -> None:
        """
        Initialize the vector service.

        Args:
            index_path: Path to the vector index (currently unused)
        """
        self.index_path = index_path
        self.initialization_error = (
            "Vector search functionality not implemented in backend structure"
        )
        logger.info("VectorService initialized (stub implementation)")

    def is_available(self) -> bool:
        """
        Check if the vector service is available.

        Returns:
            False - vector search is not currently implemented
        """
        return False

    def get_status(self) -> dict[str, str]:
        """
        Get the status of the vector service.

        Returns:
            Dictionary with status information indicating service is unavailable
        """
        return {
            "status": "unavailable",
            "error": self.initialization_error,
            "index_path": self.index_path or "not configured",
        }

    def similarity_search(self, query: str, k: int = 3) -> list[dict[str, Any]]:
        """
        Perform a similarity search.

        Args:
            query: Search query
            k: Number of results to return

        Returns:
            Empty list since search is not implemented

        Raises:
            RuntimeError: Always raises since functionality is not implemented
        """
        msg = (
            "Vector search functionality not implemented in backend structure. "
            "This feature is available in the legacy core_daemon structure."
        )
        raise RuntimeError(
            msg
        )
