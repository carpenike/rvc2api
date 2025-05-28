"""
Tests for the vector service functionality.

Tests the VectorService class which provides a placeholder implementation
for vector search functionality in the backend structure.
"""

import pytest

from backend.services.vector_service import VectorService


class TestVectorService:
    """Test cases for the VectorService class."""

    def test_init_with_index_path(self):
        """Test initialization with an index path."""
        index_path = "/path/to/vector/index"
        service = VectorService(index_path=index_path)

        assert service.index_path == index_path
        assert service.initialization_error is not None
        assert "not implemented" in service.initialization_error

    def test_init_without_index_path(self):
        """Test initialization without an index path."""
        service = VectorService()

        assert service.index_path is None
        assert service.initialization_error is not None
        assert "not implemented" in service.initialization_error

    def test_init_with_none_index_path(self):
        """Test initialization with explicit None index path."""
        service = VectorService(index_path=None)

        assert service.index_path is None
        assert service.initialization_error is not None

    def test_is_available_returns_false(self):
        """Test that is_available always returns False."""
        service = VectorService()

        assert service.is_available() is False

    def test_is_available_with_index_path(self):
        """Test that is_available returns False even with index path."""
        service = VectorService(index_path="/some/path")

        assert service.is_available() is False

    def test_get_status_without_index_path(self):
        """Test get_status when no index path is configured."""
        service = VectorService()

        status = service.get_status()

        assert isinstance(status, dict)
        assert status["status"] == "unavailable"
        assert "not implemented" in status["error"]
        assert status["index_path"] == "not configured"

    def test_get_status_with_index_path(self):
        """Test get_status when index path is configured."""
        index_path = "/configured/vector/index"
        service = VectorService(index_path=index_path)

        status = service.get_status()

        assert isinstance(status, dict)
        assert status["status"] == "unavailable"
        assert "not implemented" in status["error"]
        assert status["index_path"] == index_path

    def test_get_status_with_empty_string_index_path(self):
        """Test get_status when index path is empty string."""
        service = VectorService(index_path="")

        status = service.get_status()

        assert isinstance(status, dict)
        assert status["status"] == "unavailable"
        assert status["index_path"] == "not configured"

    def test_get_status_structure(self):
        """Test that get_status returns proper structure."""
        service = VectorService()

        status = service.get_status()

        # Verify all required keys are present
        required_keys = {"status", "error", "index_path"}
        assert set(status.keys()) == required_keys

        # Verify types
        assert isinstance(status["status"], str)
        assert isinstance(status["error"], str)
        assert isinstance(status["index_path"], str)

    def test_similarity_search_raises_runtime_error(self):
        """Test that similarity_search raises RuntimeError."""
        service = VectorService()

        with pytest.raises(RuntimeError) as exc_info:
            service.similarity_search("test query")

        error_message = str(exc_info.value)
        assert "not implemented" in error_message
        assert "backend structure" in error_message

    def test_similarity_search_with_k_parameter(self):
        """Test similarity_search raises error regardless of k parameter."""
        service = VectorService()

        with pytest.raises(RuntimeError) as exc_info:
            service.similarity_search("test query", k=5)

        error_message = str(exc_info.value)
        assert "not implemented" in error_message

    def test_similarity_search_error_message_content(self):
        """Test that similarity_search error message mentions legacy structure."""
        service = VectorService()

        with pytest.raises(RuntimeError) as exc_info:
            service.similarity_search("query")

        error_message = str(exc_info.value)
        assert "legacy core_daemon structure" in error_message
        assert "This feature is available" in error_message

    def test_multiple_service_instances(self):
        """Test that multiple service instances work independently."""
        service1 = VectorService(index_path="/path1")
        service2 = VectorService(index_path="/path2")

        assert service1.index_path != service2.index_path
        assert service1.get_status()["index_path"] == "/path1"
        assert service2.get_status()["index_path"] == "/path2"

        # Both should be unavailable
        assert not service1.is_available()
        assert not service2.is_available()

    def test_service_state_consistency(self):
        """Test that service state remains consistent across calls."""
        service = VectorService(index_path="/test/path")

        # Multiple calls should return consistent results
        status1 = service.get_status()
        status2 = service.get_status()

        assert status1 == status2
        assert service.is_available() == service.is_available()

    def test_index_path_preservation(self):
        """Test that index path is preserved correctly."""
        paths_to_test = [
            "/absolute/path",
            "relative/path",
            "path/with/spaces in it",
            "/path/with-special_chars.123",
            "",
            None,
        ]

        for path in paths_to_test:
            service = VectorService(index_path=path)
            assert service.index_path == path

            # Check status reflects the path correctly
            status = service.get_status()
            if path:
                assert status["index_path"] == path
            else:
                assert status["index_path"] == "not configured"

    def test_error_message_consistency(self):
        """Test that error messages are consistent across instances."""
        service1 = VectorService()
        service2 = VectorService(index_path="/some/path")

        # Both should have the same initialization error
        assert service1.initialization_error == service2.initialization_error

        # Status errors should be the same
        status1 = service1.get_status()
        status2 = service2.get_status()
        assert status1["error"] == status2["error"]

    def test_similarity_search_different_queries(self):
        """Test that similarity_search fails consistently for different queries."""
        service = VectorService()

        queries = ["", "short", "a much longer query with multiple words", "special!@#$%^&*()chars"]

        for query in queries:
            with pytest.raises(RuntimeError) as exc_info:
                service.similarity_search(query)

            # All should have the same error message
            assert "not implemented" in str(exc_info.value)

    def test_similarity_search_different_k_values(self):
        """Test that similarity_search fails for different k values."""
        service = VectorService()

        k_values = [1, 3, 5, 10, 100]

        for k in k_values:
            with pytest.raises(RuntimeError):
                service.similarity_search("test", k=k)

    def test_service_methods_return_types(self):
        """Test that all service methods return expected types."""
        service = VectorService()

        # is_available should return bool
        available = service.is_available()
        assert isinstance(available, bool)

        # get_status should return dict
        status = service.get_status()
        assert isinstance(status, dict)

        # similarity_search should raise, not return
        with pytest.raises(RuntimeError):
            service.similarity_search("test")
