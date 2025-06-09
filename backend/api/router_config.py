#!/usr/bin/env python3
"""
Router Configuration

Router configuration that uses FastAPI dependency injection for service management.
"""

import logging
from typing import Any

from fastapi import FastAPI

from backend.api.routers import (
    advanced_diagnostics,
    can,
    config,
    dashboard,
    docs,
    entities,
    logs,
    multi_network,
    performance_analytics,
)
from backend.websocket.routes import router as websocket_router

logger = logging.getLogger(__name__)


def configure_routers(app: FastAPI) -> None:
    """
    Configure all API routers using dependency injection.

    This approach relies on FastAPI's dependency injection system,
    allowing services to be injected as needed by route handlers.

    Args:
        app: FastAPI application instance
    """
    logger.info("Configuring API routers with dependency injection")

    # Include all routers - they will use dependency injection internally
    app.include_router(entities.router)
    app.include_router(can.router)
    app.include_router(config.router)
    app.include_router(dashboard.router)
    app.include_router(docs.router)
    app.include_router(logs.router)
    app.include_router(multi_network.router)
    app.include_router(advanced_diagnostics.router, prefix="/api/diagnostics", tags=["diagnostics"])
    app.include_router(
        performance_analytics.router, prefix="/api/performance", tags=["performance"]
    )

    # Include WebSocket routes that integrate with feature manager
    app.include_router(websocket_router)

    logger.info("All API routers configured successfully")


def get_router_info() -> dict[str, Any]:
    """
    Get information about all configured routers.

    Returns:
        Dictionary with router information including prefixes and tags
    """
    return {
        "routers": [
            {"prefix": "/api", "tags": ["entities"], "name": "entities"},
            {"prefix": "/api", "tags": ["can"], "name": "can"},
            {"prefix": "/api", "tags": ["config"], "name": "config"},
            {"prefix": "/api/dashboard", "tags": ["dashboard"], "name": "dashboard"},
            {"prefix": "/api", "tags": ["docs"], "name": "docs"},
            {"prefix": "/api", "tags": ["logs"], "name": "logs"},
            {"prefix": "/api/multi-network", "tags": ["multi-network"], "name": "multi_network"},
            {"prefix": "/api/diagnostics", "tags": ["diagnostics"], "name": "advanced_diagnostics"},
            {
                "prefix": "/api/performance",
                "tags": ["performance"],
                "name": "performance_analytics",
            },
            {"prefix": "/ws", "tags": ["websocket"], "name": "websocket"},
        ],
        "total_routers": 10,
        "dependency_injection": True,
    }
