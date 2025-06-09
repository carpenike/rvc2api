"""
Core dependencies for dependency injection.

This module provides functions to access the application state and services
from FastAPI's dependency injection system.
"""

import logging
from typing import Any

from fastapi import Request

logger = logging.getLogger(__name__)


def get_app_state(request: Request) -> Any:
    """
    Get the application state from the FastAPI application state.

    Args:
        request: The FastAPI request object

    Returns:
        The application state

    Raises:
        RuntimeError: If the app state is not initialized
    """
    if not hasattr(request.app.state, "app_state"):
        raise RuntimeError("Application state not initialized")
    return request.app.state.app_state


def get_entity_service(request: Request) -> Any:
    """
    Get the entity service from the FastAPI application state.

    Args:
        request: The FastAPI request object

    Returns:
        The entity service

    Raises:
        RuntimeError: If the entity service is not initialized
    """
    if not hasattr(request.app.state, "entity_service"):
        raise RuntimeError("Entity service not initialized")
    return request.app.state.entity_service


def get_can_service(request: Request) -> Any:
    """
    Get the CAN service from the FastAPI application state.

    Args:
        request: The FastAPI request object

    Returns:
        The CAN service

    Raises:
        RuntimeError: If the CAN service is not initialized
    """
    if not hasattr(request.app.state, "can_service"):
        raise RuntimeError("CAN service not initialized")
    return request.app.state.can_service


def get_feature_manager_from_request(request: Request) -> Any:
    """
    Get the feature manager from the FastAPI application state.

    Args:
        request: The FastAPI request object

    Returns:
        The feature manager

    Raises:
        RuntimeError: If the feature manager is not initialized
    """
    if not hasattr(request.app.state, "feature_manager"):
        raise RuntimeError("Feature manager not initialized")
    return request.app.state.feature_manager


def get_config_service(request: Request) -> Any:
    """
    Get the config service from the FastAPI application state.

    Args:
        request: The FastAPI request object

    Returns:
        The config service

    Raises:
        RuntimeError: If the config service is not initialized
    """
    if not hasattr(request.app.state, "config_service"):
        raise RuntimeError("Config service not initialized")
    return request.app.state.config_service


def get_docs_service(request: Request) -> Any:
    """
    Get the docs service from the FastAPI application state.

    Args:
        request: The FastAPI request object

    Returns:
        The docs service

    Raises:
        RuntimeError: If the docs service is not initialized
    """
    if not hasattr(request.app.state, "docs_service"):
        raise RuntimeError("Docs service not initialized")
    return request.app.state.docs_service


def get_vector_service(request: Request) -> Any:
    """
    Get the vector service from the FastAPI application state.

    Args:
        request: The FastAPI request object

    Returns:
        The vector service

    Raises:
        RuntimeError: If the vector service is not initialized
    """
    if not hasattr(request.app.state, "vector_service"):
        raise RuntimeError("Vector service not initialized")
    return request.app.state.vector_service


def get_github_update_checker(request: Request) -> Any:
    """
    Get the GitHub update checker feature from the feature manager.

    Args:
        request: The FastAPI request object

    Returns:
        The GitHub update checker feature

    Raises:
        RuntimeError: If the feature manager is not initialized or the feature is not found
    """
    feature_manager = get_feature_manager_from_request(request)
    if "github_update_checker" not in feature_manager.features:
        raise RuntimeError("GitHub update checker feature not found")

    update_checker_feature = feature_manager.features["github_update_checker"]
    if not getattr(update_checker_feature, "enabled", False):
        raise RuntimeError("GitHub update checker feature is not enabled")

    return update_checker_feature.get_update_checker()


def get_can_interface_service(request: Request) -> Any:
    """
    Get the CAN interface service from the FastAPI application state.

    Args:
        request: The FastAPI request object

    Returns:
        The CAN interface service

    Raises:
        RuntimeError: If the CAN interface service is not initialized
    """
    if not hasattr(request.app.state, "can_interface_service"):
        raise RuntimeError("CAN interface service not initialized")
    return request.app.state.can_interface_service


def get_websocket_manager(request: Request) -> Any:
    """
    Get the WebSocket manager from the feature manager.

    Args:
        request: The FastAPI request object

    Returns:
        The WebSocket manager

    Raises:
        RuntimeError: If the feature manager is not initialized or websocket feature is not found
    """
    feature_manager = get_feature_manager_from_request(request)
    websocket_feature = feature_manager.get_feature("websocket")
    if not websocket_feature:
        raise RuntimeError("WebSocket feature not found or not enabled")
    return websocket_feature


def get_persistence_service(request: Request) -> Any:
    """
    Get the persistence service from the FastAPI application state.

    Args:
        request: The FastAPI request object

    Returns:
        The persistence service

    Raises:
        RuntimeError: If the persistence service is not initialized
    """
    if not hasattr(request.app.state, "persistence_service"):
        raise RuntimeError("Persistence service not initialized")
    return request.app.state.persistence_service


def get_database_manager(request: Request) -> Any:
    """
    Get the database manager from the FastAPI application state.

    Args:
        request: The FastAPI request object

    Returns:
        The database manager

    Raises:
        RuntimeError: If the database manager is not initialized
    """
    if not hasattr(request.app.state, "database_manager"):
        raise RuntimeError("Database manager not initialized")
    return request.app.state.database_manager


def get_config_repository(request: Request) -> Any:
    """
    Get the configuration repository from the FastAPI application state.

    Args:
        request: The FastAPI request object

    Returns:
        The configuration repository

    Raises:
        RuntimeError: If the configuration repository is not initialized
    """
    if not hasattr(request.app.state, "config_repository"):
        raise RuntimeError("Configuration repository not initialized")
    return request.app.state.config_repository


def get_dashboard_repository(request: Request) -> Any:
    """
    Get the dashboard repository from the FastAPI application state.

    Args:
        request: The FastAPI request object

    Returns:
        The dashboard repository

    Raises:
        RuntimeError: If the dashboard repository is not initialized
    """
    if not hasattr(request.app.state, "dashboard_repository"):
        raise RuntimeError("Dashboard repository not initialized")
    return request.app.state.dashboard_repository


def get_auth_manager(request: Request = None) -> Any:
    """
    Get the authentication manager from the feature manager.

    Args:
        request: The FastAPI request object (optional)

    Returns:
        The authentication manager

    Raises:
        RuntimeError: If the feature manager is not initialized or auth feature is not found
    """
    # Import here to avoid circular imports
    from backend.services.feature_manager import get_feature_manager

    if request:
        feature_manager = get_feature_manager_from_request(request)
    else:
        feature_manager = get_feature_manager()

    auth_feature = feature_manager.get_feature("authentication")
    if not auth_feature:
        raise RuntimeError("Authentication feature not found or not enabled")

    auth_manager = auth_feature.get_auth_manager()
    if not auth_manager:
        raise RuntimeError("Authentication manager not initialized")

    return auth_manager


def get_notification_manager(request: Request = None) -> Any:
    """
    Get the notification manager from the feature manager.

    Args:
        request: The FastAPI request object (optional)

    Returns:
        The notification manager or None if not available

    Raises:
        RuntimeError: If the feature manager is not initialized
    """
    # Import here to avoid circular imports
    from backend.services.feature_manager import get_feature_manager

    if request:
        feature_manager = get_feature_manager_from_request(request)
    else:
        feature_manager = get_feature_manager()

    notification_feature = feature_manager.get_feature("notifications")
    if not notification_feature:
        return None  # Notification manager is optional

    return notification_feature.get_notification_manager()


def get_bulk_operations_service(request: Request) -> Any:
    """
    Get the bulk operations service from the FastAPI application state.

    Args:
        request: The FastAPI request object

    Returns:
        The bulk operations service

    Raises:
        RuntimeError: If the bulk operations service is not initialized
    """
    if not hasattr(request.app.state, "bulk_operations_service"):
        raise RuntimeError("Bulk operations service not initialized")
    return request.app.state.bulk_operations_service


def get_predictive_maintenance_service(request: Request) -> Any:
    """
    Get the predictive maintenance service from the FastAPI application state.

    Args:
        request: The FastAPI request object

    Returns:
        The predictive maintenance service

    Raises:
        RuntimeError: If the predictive maintenance service is not initialized
    """
    if not hasattr(request.app.state, "predictive_maintenance_service"):
        raise RuntimeError("Predictive maintenance service not initialized")
    return request.app.state.predictive_maintenance_service
