"""
Tests for the vector service module.

These tests verify the behavior of the vector service functionality,
including handling of initialization errors and search operations.
"""

import os
from unittest import mock

import pytest
from core_daemon.services.vector_service import (
    DEFAULT_EMBEDDING_MODEL,
    VectorService,
    get_vector_service,
)


class TestVectorService:
    """Test suite for VectorService."""

    def setup_method(self):
        """Set up test environment before each test."""
        # Ensure we're using a clean cache for get_vector_service
        get_vector_service.cache_clear()

    @mock.patch("core_daemon.services.vector_service.FAISS")
    @mock.patch("core_daemon.services.vector_service.OpenAIEmbeddings")
    @mock.patch("core_daemon.services.vector_service.Path.exists")
    @mock.patch.dict(os.environ, {"OPENAI_API_KEY": "mock-api-key"})
    def test_successful_initialization(self, mock_exists, mock_embeddings, mock_faiss):
        """Test successful initialization of VectorService."""
        # Setup
        mock_exists.return_value = True
        mock_embeddings_instance = mock.MagicMock()
        mock_embeddings.return_value = mock_embeddings_instance
        mock_vectorstore = mock.MagicMock()
        mock_faiss.load_local.return_value = mock_vectorstore

        # Execute
        service = VectorService(index_path="test/path")

        # Verify
        assert service.is_available() is True
        assert service.vectorstore is not None
        assert service.initialization_error is None
        mock_faiss.load_local.assert_called_once_with("test/path", mock_embeddings_instance)

    @mock.patch("core_daemon.services.vector_service.Path.exists")
    @mock.patch.dict(os.environ, {}, clear=True)  # Clear environment variables
    def test_initialization_without_api_key(self, mock_exists):
        """Test initialization when OpenAI API key is missing."""
        # Setup
        mock_exists.return_value = True

        # Execute
        service = VectorService(index_path="test/path")

        # Verify
        assert service.is_available() is False
        assert service.initialization_error == "OPENAI_API_KEY environment variable not set"
        assert service.vectorstore is None

    @mock.patch("core_daemon.services.vector_service.Path.exists")
    @mock.patch.dict(os.environ, {"OPENAI_API_KEY": "mock-api-key"})
    def test_initialization_with_missing_index(self, mock_exists):
        """Test initialization when FAISS index directory is missing."""
        # Setup
        mock_exists.return_value = False

        # Execute
        service = VectorService(index_path="nonexistent/path")

        # Verify
        assert service.is_available() is False
        assert service.initialization_error == "FAISS index not found at nonexistent/path"
        assert service.vectorstore is None

    @mock.patch("core_daemon.services.vector_service.FAISS")
    @mock.patch("core_daemon.services.vector_service.OpenAIEmbeddings")
    @mock.patch("core_daemon.services.vector_service.Path.exists")
    @mock.patch.dict(os.environ, {"OPENAI_API_KEY": "mock-api-key"})
    def test_initialization_with_load_error(self, mock_exists, mock_embeddings, mock_faiss):
        """Test initialization when FAISS index loading fails."""
        # Setup
        mock_exists.return_value = True
        mock_embeddings_instance = mock.MagicMock()
        mock_embeddings.return_value = mock_embeddings_instance
        mock_faiss.load_local.side_effect = Exception("Load error")

        # Execute
        service = VectorService(index_path="test/path")

        # Verify
        assert service.is_available() is False
        assert service.initialization_error is not None
        assert service.initialization_error == "Failed to load FAISS index: Load error"
        assert service.vectorstore is None

    @mock.patch("core_daemon.services.vector_service.FAISS")
    @mock.patch("core_daemon.services.vector_service.OpenAIEmbeddings")
    @mock.patch("core_daemon.services.vector_service.Path.exists")
    @mock.patch.dict(os.environ, {"OPENAI_API_KEY": "mock-api-key"})
    def test_get_status_available(self, mock_exists, mock_embeddings, mock_faiss):
        """Test get_status when service is available."""
        # Setup
        mock_exists.return_value = True
        mock_embeddings_instance = mock.MagicMock()
        mock_embeddings.return_value = mock_embeddings_instance
        mock_faiss.load_local.return_value = mock.MagicMock()

        # Execute
        service = VectorService(index_path="test/path")
        status = service.get_status()

        # Verify
        assert status == {
            "status": "available",
            "index_path": "test/path",
            "embedding_model": DEFAULT_EMBEDDING_MODEL,
        }

    @mock.patch("core_daemon.services.vector_service.Path.exists")
    @mock.patch.dict(os.environ, {}, clear=True)
    def test_get_status_unavailable(self, mock_exists):
        """Test get_status when service is unavailable."""
        # Setup
        mock_exists.return_value = True

        # Execute
        service = VectorService(index_path="test/path")
        status = service.get_status()

        # Verify
        assert status == {
            "status": "unavailable",
            "error": "OPENAI_API_KEY environment variable not set",
            "index_path": "test/path",
        }

    @mock.patch("core_daemon.services.vector_service.FAISS")
    @mock.patch("core_daemon.services.vector_service.OpenAIEmbeddings")
    @mock.patch("core_daemon.services.vector_service.Path.exists")
    @mock.patch.dict(os.environ, {"OPENAI_API_KEY": "mock-api-key"})
    def test_similarity_search_success(self, mock_exists, mock_embeddings, mock_faiss):
        """Test successful similarity search."""
        # Setup
        mock_exists.return_value = True
        mock_embeddings_instance = mock.MagicMock()
        mock_embeddings.return_value = mock_embeddings_instance
        mock_vectorstore = mock.MagicMock()
        mock_faiss.load_local.return_value = mock_vectorstore

        # Create mock search results
        mock_doc1 = mock.MagicMock()
        mock_doc1.page_content = "Test content 1"
        mock_doc1.metadata = {
            "section": "1.1",
            "title": "Test Title 1",
            "pages": [1, 2],
        }

        mock_doc2 = mock.MagicMock()
        mock_doc2.page_content = "Test content 2"
        mock_doc2.metadata = {
            "section": "1.2",
            "title": "Test Title 2",
            "pages": [3, 4],
        }

        mock_vectorstore.similarity_search.return_value = [mock_doc1, mock_doc2]

        # Execute
        service = VectorService(index_path="test/path")
        results = service.similarity_search("test query", k=2)

        # Verify
        assert len(results) == 2
        assert results[0]["content"] == "Test content 1"
        assert results[0]["section"] == "1.1"
        assert results[0]["title"] == "Test Title 1"
        assert results[0]["pages"] == [1, 2]
        mock_vectorstore.similarity_search.assert_called_once_with("test query", k=2)

    @mock.patch("core_daemon.services.vector_service.Path.exists")
    @mock.patch.dict(os.environ, {}, clear=True)
    def test_similarity_search_unavailable(self, mock_exists):
        """Test similarity search when service is unavailable."""
        # Setup
        mock_exists.return_value = True
        service = VectorService(index_path="test/path")

        # Execute & Verify
        with pytest.raises(RuntimeError, match="Vector search is not available"):
            service.similarity_search("test query")

    @mock.patch("core_daemon.services.vector_service.FAISS")
    @mock.patch("core_daemon.services.vector_service.OpenAIEmbeddings")
    @mock.patch("core_daemon.services.vector_service.Path.exists")
    @mock.patch.dict(os.environ, {"OPENAI_API_KEY": "mock-api-key"})
    def test_similarity_search_exception(self, mock_exists, mock_embeddings, mock_faiss):
        """Test similarity search handling exceptions."""
        # Setup
        mock_exists.return_value = True
        mock_embeddings_instance = mock.MagicMock()
        mock_embeddings.return_value = mock_embeddings_instance
        mock_vectorstore = mock.MagicMock()
        mock_faiss.load_local.return_value = mock_vectorstore
        mock_vectorstore.similarity_search.side_effect = Exception("Search failed")

        # Execute
        service = VectorService(index_path="test/path")
        results = service.similarity_search("test query")

        # Verify
        assert results == []

    @mock.patch("core_daemon.services.vector_service.VectorService")
    def test_get_vector_service_caching(self, mock_vector_service):
        """Test that get_vector_service uses caching."""
        # Setup
        mock_instance = mock.MagicMock()
        mock_vector_service.return_value = mock_instance

        # Execute - call twice with same parameters
        service1 = get_vector_service("same/path")
        service2 = get_vector_service("same/path")

        # Verify
        assert service1 is service2  # Should be the same instance due to caching
        mock_vector_service.assert_called_once()  # Constructor should only be called once

    @mock.patch("core_daemon.services.vector_service.VectorService")
    def test_get_vector_service_different_paths(self, mock_vector_service):
        """Test that get_vector_service creates different instances for different paths."""
        # Setup
        mock_vector_service.side_effect = lambda **kwargs: mock.MagicMock(**kwargs)

        # Execute
        service1 = get_vector_service("path1")
        service2 = get_vector_service("path2")

        # Verify
        assert service1 is not service2  # Should be different instances
        assert mock_vector_service.call_count == 2
