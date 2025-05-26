"""
Vector service for FAISS embeddings in the rvc2api daemon.

This module provides vector search capabilities using FAISS indices to enable
semantic searching of RV-C documentation.

Implementation follows a singleton pattern with caching to efficiently manage
vector database resources throughout the application lifecycle.
"""

import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

logger = logging.getLogger(__name__)

# Default paths and configurations
DEFAULT_VECTOR_STORE_DIR = os.path.join("resources", "vector_store")
DEFAULT_INDEX_NAME = "rvc_spec_index"
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-large"


class VectorService:
    """Service for managing vector embeddings and semantic search with FAISS indices."""

    def __init__(
        self,
        index_path: str,
        embedding_model: str = DEFAULT_EMBEDDING_MODEL,
    ) -> None:
        """
        Initialize the vector service with the given FAISS index.

        Args:
            index_path: Path to the FAISS index directory
            embedding_model: Name of the OpenAI embedding model to use

        Raises:
            FileNotFoundError: If FAISS index doesn't exist
            ValueError: If unable to load the FAISS index
            RuntimeError: If OpenAI API key is not available
        """
        self.index_path = index_path
        self.embedding_model = embedding_model
        self.vectorstore = None
        self.initialization_error = None

        # Check for OpenAI API key
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            error_msg = "OPENAI_API_KEY environment variable not set"
            self.initialization_error = error_msg
            logger.warning(f"{error_msg}. Vector search functionality will not be available.")
            return

        # Validate and load FAISS index
        if not Path(index_path).exists():
            error_msg = f"FAISS index not found at {index_path}"
            self.initialization_error = error_msg
            logger.error(error_msg)
            return

        try:
            self.embeddings = OpenAIEmbeddings(model=embedding_model)
            self.vectorstore = FAISS.load_local(index_path, self.embeddings)
            logger.info(
                f"FAISS index loaded successfully from {index_path} using model {embedding_model}"
            )
        except Exception as e:
            error_msg = f"Failed to load FAISS index: {e}"
            self.initialization_error = error_msg
            logger.error(error_msg)

    def is_available(self) -> bool:
        """
        Check if the vector service is properly initialized and available.

        Returns:
            bool: True if the service is available, False otherwise
        """
        return self.vectorstore is not None

    def get_status(self) -> dict[str, str]:
        """
        Get the status of the vector service including any initialization errors.

        Returns:
            dict: Dictionary with status information
        """
        if self.is_available():
            return {
                "status": "available",
                "index_path": self.index_path,
                "embedding_model": self.embedding_model,
            }

        return {
            "status": "unavailable",
            "error": self.initialization_error or "Unknown initialization error",
            "index_path": self.index_path,
        }

    def similarity_search(
        self,
        query: str,
        k: int = 3,
    ) -> list[dict[str, Any]]:
        """
        Perform a similarity search on the FAISS index.

        Args:
            query: The search query string
            k: Number of results to return

        Returns:
            List of dictionaries containing matched documents with metadata

        Raises:
            RuntimeError: If vector search is not available
        """
        if not self.is_available():
            error_msg = (
                f"Vector search is not available: {self.initialization_error or 'Unknown error'}"
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        try:
            # self.vectorstore will never be None here because is_available() check above ensures it
            assert self.vectorstore is not None
            results = self.vectorstore.similarity_search(query, k=k)

            # Format results
            formatted_results = []
            for doc in results:
                formatted_results.append(
                    {
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "section": doc.metadata.get("section"),
                        "title": doc.metadata.get("title"),
                        "pages": doc.metadata.get("pages", []),
                    }
                )

            return formatted_results
        except Exception as e:
            logger.error(f"Error performing similarity search: {e}")
            return []


@lru_cache
def get_vector_service(
    index_path: str | None = None,
    embedding_model: str = DEFAULT_EMBEDDING_MODEL,
) -> VectorService:
    """
    Get or create a VectorService instance (singleton pattern with caching).

    Args:
        index_path: Optional custom path to the FAISS index
        embedding_model: Name of the OpenAI embedding model to use

    Returns:
        VectorService: The initialized vector service
    """
    if index_path is None:
        # Use default path
        index_path = os.path.join(DEFAULT_VECTOR_STORE_DIR, DEFAULT_INDEX_NAME)

    # Create a new vector service instance
    return VectorService(index_path=index_path, embedding_model=embedding_model)
