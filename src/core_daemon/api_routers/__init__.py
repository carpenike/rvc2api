"""
api_routers

This package contains FastAPI APIRouter modules that define the various API endpoints
for the rvc2api application. Each router handles a specific domain of functionality
to maintain separation of concerns.

Routers:
    - can: Endpoints for CAN bus operations and message handling
    - config_and_ws: Configuration and WebSocket connection endpoints
    - docs: Endpoints for RV-C documentation search
    - entities: Endpoints for interacting with RV-C entities
"""

from core_daemon.api_routers.can import api_router_can
from core_daemon.api_routers.config_and_ws import api_router_config_ws
from core_daemon.api_routers.docs import router as api_router_docs
from core_daemon.api_routers.entities import api_router_entities

__all__ = ["api_router_can", "api_router_config_ws", "api_router_docs", "api_router_entities"]
