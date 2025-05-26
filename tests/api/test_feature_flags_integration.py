"""
Tests for feature flag integration in API routers.

This module verifies that API endpoints correctly respect feature flags,
returning 404 when required features are disabled and functioning normally
when features are enabled.
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from backend.main import create_app


@pytest.fixture
def mock_feature_manager():
    """Create a mock feature manager for testing."""
    mock = Mock()

    # Configure the methods that are actually used by FeatureManager
    mock.is_enabled = Mock(return_value=True)
    mock.get_all_features = Mock(return_value={})
    mock.get_enabled_features = Mock(return_value={})
    mock.get_core_features = Mock(return_value={})
    mock.get_optional_features = Mock(return_value={})

    return mock


@pytest.fixture
def app_with_mock_features(mock_feature_manager):
    """Create an app with a mock feature manager."""
    # Create mock services with default return values
    mock_can_service = Mock()
    mock_can_service.get_queue_status = AsyncMock(return_value={"status": "ok"})
    mock_can_service.send_frame = AsyncMock(return_value={"success": True})

    mock_entity_service = Mock()
    # Set up async methods to return the expected values
    mock_entity_service.list_entities = AsyncMock(return_value={})
    mock_entity_service.list_entity_ids = AsyncMock(return_value=[])
    mock_entity_service.get_lights = AsyncMock(return_value=[])
    mock_entity_service.get_locks = AsyncMock(return_value=[])
    mock_entity_service.get_entity_by_id = AsyncMock(return_value=None)

    mock_config_service = Mock()
    mock_config_service.get_config = AsyncMock(return_value={})
    mock_config_service.update_config = AsyncMock(return_value={"success": True})

    mock_docs_service = Mock()
    mock_docs_service.get_api_schema = AsyncMock(return_value={})

    mock_vector_service = Mock()
    # Set up both sync and async methods properly
    mock_vector_service.get_status.return_value = {"initialized": True, "documents": 0}
    mock_vector_service.is_available.return_value = True
    mock_vector_service.get_network_status.return_value = {"status": "disconnected"}

    mock_app_state = Mock()

    # Mock the services to avoid actual initialization
    with (
        patch("backend.core.state.AppState"),
        patch(
            "backend.services.feature_manager.get_feature_manager",
            return_value=mock_feature_manager,
        ),
        patch("backend.services.can_service.CANService"),
        patch("backend.services.entity_service.EntityService"),
        patch("backend.services.config_service.ConfigService"),
        patch("backend.services.rvc_service.RVCService"),
        patch("backend.websocket.handlers.WebSocketManager"),
        # Patch all dependency injection functions to return mock services
        patch(
            "backend.core.dependencies.get_feature_manager_from_request",
            return_value=mock_feature_manager,
        ),
        patch(
            "backend.core.dependencies.get_can_service",
            return_value=mock_can_service,
        ),
        patch(
            "backend.core.dependencies.get_entity_service",
            return_value=mock_entity_service,
        ),
        patch(
            "backend.core.dependencies.get_config_service",
            return_value=mock_config_service,
        ),
        patch(
            "backend.core.dependencies.get_docs_service",
            return_value=mock_docs_service,
        ),
        patch(
            "backend.core.dependencies.get_vector_service",
            return_value=mock_vector_service,
        ),
        patch(
            "backend.core.dependencies.get_app_state",
            return_value=mock_app_state,
        ),
    ):
        app = create_app()
        # Inject mock services into app state
        app.state.feature_manager = mock_feature_manager
        app.state.can_service = mock_can_service
        app.state.entity_service = mock_entity_service
        app.state.config_service = mock_config_service
        app.state.docs_service = mock_docs_service
        app.state.vector_service = mock_vector_service
        app.state.app_state = mock_app_state
        return app


@pytest.fixture
def client_with_mock_features(app_with_mock_features):
    """Create a test client with mock feature manager."""
    return TestClient(app_with_mock_features)


class TestCANRouterFeatureFlags:
    """Test feature flag integration for CAN router endpoints."""

    def test_can_endpoints_available_when_canbus_enabled(
        self, client_with_mock_features, mock_feature_manager
    ):
        """Test that CAN endpoints are available when can_interface feature is enabled."""
        mock_feature_manager.is_enabled.return_value = True

        response = client_with_mock_features.get("/api/can/queue/status")

        # Should succeed with 200
        assert response.status_code == 200
        # Should have checked can_interface feature
        mock_feature_manager.is_enabled.assert_called_with("can_interface")

    def test_can_endpoints_unavailable_when_canbus_disabled(
        self, client_with_mock_features, mock_feature_manager
    ):
        """Test that CAN endpoints return 404 when can_interface feature is disabled."""
        mock_feature_manager.is_enabled.return_value = False

        response = client_with_mock_features.get("/api/can/queue/status")

        # Should return 404
        assert response.status_code == 404
        assert "can_interface feature is disabled" in response.json()["detail"]
        # Should have checked can_interface feature
        mock_feature_manager.is_enabled.assert_called_with("can_interface")

    def test_all_can_endpoints_respect_feature_flag(
        self, client_with_mock_features, mock_feature_manager
    ):
        """Test that all CAN endpoints respect the can_interface feature flag."""
        mock_feature_manager.is_enabled.return_value = False

        can_endpoints = [
            "/api/can/queue/status",
            "/api/can/interfaces",
            "/api/can/interfaces/details",
            "/api/can/statistics",
        ]

        for endpoint in can_endpoints:
            response = client_with_mock_features.get(endpoint)
            assert (
                response.status_code == 404
            ), f"Endpoint {endpoint} should return 404 when can_interface disabled"
            assert "can_interface feature is disabled" in response.json()["detail"]


class TestEntitiesRouterFeatureFlags:
    """Test feature flag integration for Entities router endpoints."""

    def test_entities_endpoints_available_when_rvc_enabled(
        self, client_with_mock_features, mock_feature_manager
    ):
        """Test that entities endpoints are available when rvc feature is enabled."""
        mock_feature_manager.is_enabled.return_value = True

        response = client_with_mock_features.get("/api/entities")

        # Should succeed with 200
        assert response.status_code == 200
        # Should have checked rvc feature
        mock_feature_manager.is_enabled.assert_called_with("rvc")

    def test_entities_endpoints_unavailable_when_rvc_disabled(
        self, client_with_mock_features, mock_feature_manager
    ):
        """Test that entities endpoints return 404 when rvc feature is disabled."""
        mock_feature_manager.is_enabled.return_value = False

        response = client_with_mock_features.get("/api/entities")

        # Should return 404
        assert response.status_code == 404
        assert "rvc feature is disabled" in response.json()["detail"]
        # Should have checked rvc feature
        mock_feature_manager.is_enabled.assert_called_with("rvc")

    def test_all_entities_endpoints_respect_feature_flag(
        self, client_with_mock_features, mock_feature_manager
    ):
        """Test that all entities endpoints respect the rvc feature flag."""
        mock_feature_manager.is_enabled.return_value = False

        entities_endpoints = [
            "/api/entities",
            "/api/entities/ids",
            "/api/unmapped",
            "/api/unknown-pgns",
            "/api/metadata",
        ]

        for endpoint in entities_endpoints:
            response = client_with_mock_features.get(endpoint)
            assert (
                response.status_code == 404
            ), f"Endpoint {endpoint} should return 404 when rvc disabled"
            assert "rvc feature is disabled" in response.json()["detail"]


class TestDocsRouterFeatureFlags:
    """Test feature flag integration for Docs router endpoints."""

    def test_docs_endpoints_available_when_api_docs_enabled(
        self, client_with_mock_features, mock_feature_manager
    ):
        """Test that docs endpoints are available when api_docs feature is enabled."""
        mock_feature_manager.is_enabled.return_value = True

        response = client_with_mock_features.get("/api/docs/status")

        # Should succeed with 200
        assert response.status_code == 200
        # Should have checked api_docs feature
        mock_feature_manager.is_enabled.assert_called_with("api_docs")

    def test_docs_endpoints_unavailable_when_api_docs_disabled(
        self, client_with_mock_features, mock_feature_manager
    ):
        """Test that docs endpoints return 404 when api_docs feature is disabled."""
        mock_feature_manager.is_enabled.return_value = False

        response = client_with_mock_features.get("/api/docs/status")

        # Should return 404
        assert response.status_code == 404
        assert "api_docs feature is disabled" in response.json()["detail"]
        # Should have checked api_docs feature
        mock_feature_manager.is_enabled.assert_called_with("api_docs")


class TestConfigRouterFeatureStatus:
    """Test the new feature status endpoint in config router."""

    def test_features_status_endpoint(self, client_with_mock_features, mock_feature_manager):
        """Test that the features status endpoint works correctly."""
        # Create mock feature objects with the expected attributes
        from unittest.mock import Mock

        mock_canbus = Mock()
        mock_canbus.enabled = True
        mock_canbus.core = True
        mock_canbus.health = "healthy"
        mock_canbus.feature_type = "integration"

        mock_rvc = Mock()
        mock_rvc.enabled = True
        mock_rvc.core = True
        mock_rvc.health = "healthy"
        mock_rvc.feature_type = "decoder"

        mock_api_docs = Mock()
        mock_api_docs.enabled = False
        mock_api_docs.core = False
        mock_api_docs.health = "disabled"
        mock_api_docs.feature_type = "interface"

        # Mock feature manager methods using actual available methods
        all_features = {
            "canbus": mock_canbus,
            "rvc": mock_rvc,
            "api_docs": mock_api_docs,
        }
        enabled_features = {
            "canbus": mock_canbus,
            "rvc": mock_rvc,
        }
        core_features = {
            "canbus": mock_canbus,
            "rvc": mock_rvc,
        }
        optional_features = {
            "api_docs": mock_api_docs,
        }

        mock_feature_manager.get_all_features.return_value = all_features
        mock_feature_manager.get_enabled_features.return_value = enabled_features
        mock_feature_manager.get_core_features.return_value = core_features
        mock_feature_manager.get_optional_features.return_value = optional_features

        response = client_with_mock_features.get("/api/status/features")

        assert response.status_code == 200
        data = response.json()

        # Check summary stats calculated from the actual methods (note the key name changes)
        assert data["total_features"] == 3
        assert data["enabled_count"] == 2  # Changed from enabled_features
        assert data["core_count"] == 2  # Changed from core_features
        assert data["optional_count"] == 1  # Changed from optional_features

        # Check individual feature status
        assert "canbus" in data["features"]
        assert data["features"]["canbus"]["enabled"] is True
        assert data["features"]["canbus"]["core"] is True
        assert data["features"]["canbus"]["health"] == "healthy"

        assert "api_docs" in data["features"]
        assert data["features"]["api_docs"]["enabled"] is False
        assert data["features"]["api_docs"]["core"] is False
        assert data["features"]["api_docs"]["health"] == "disabled"
