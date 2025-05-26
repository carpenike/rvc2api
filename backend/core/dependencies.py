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
