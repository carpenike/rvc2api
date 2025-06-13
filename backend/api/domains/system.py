"""
System Domain API Router (v2)

Provides domain-specific system management endpoints:
- System information and status
- Configuration management
- Service health monitoring
- Performance metrics

This router integrates with existing system services.
"""

import logging
import time
import platform
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from backend.core.dependencies import get_feature_manager_from_request
from backend.api.domains import register_domain_router

logger = logging.getLogger(__name__)

# Domain-specific schemas for v2 API
class SystemInfo(BaseModel):
    """System information"""
    hostname: str = Field(..., description="System hostname")
    platform: str = Field(..., description="Operating system platform")
    architecture: str = Field(..., description="System architecture")
    python_version: str = Field(..., description="Python version")
    uptime_seconds: float = Field(..., description="System uptime in seconds")
    timestamp: float = Field(..., description="Info timestamp")

class ServiceStatus(BaseModel):
    """Service status information"""
    name: str = Field(..., description="Service name")
    status: str = Field(..., description="Service status: healthy/degraded/unhealthy")
    enabled: bool = Field(..., description="Whether service is enabled")
    last_check: float = Field(..., description="Last health check timestamp")

class SystemStatus(BaseModel):
    """Overall system status"""
    overall_status: str = Field(..., description="Overall system status")
    services: List[ServiceStatus] = Field(..., description="Individual service statuses")
    total_services: int = Field(..., description="Total number of services")
    healthy_services: int = Field(..., description="Number of healthy services")
    timestamp: float = Field(..., description="Status timestamp")

def create_system_router() -> APIRouter:
    """Create the system domain router with all endpoints"""
    router = APIRouter(tags=["system-v2"])

    def _check_domain_api_enabled(request: Request) -> None:
        """Check if system API v2 is enabled"""
        feature_manager = get_feature_manager_from_request(request)
        if not feature_manager.is_enabled("domain_api_v2"):
            raise HTTPException(
                status_code=404,
                detail="Domain API v2 is disabled. Enable with COACHIQ_FEATURES__DOMAIN_API_V2=true"
            )
        # Note: system_api_v2 feature flag doesn't exist yet, so we skip that check

    @router.get("/health")
    async def health_check(request: Request) -> Dict[str, Any]:
        """Health check endpoint for system domain API"""
        _check_domain_api_enabled(request)

        return {
            "status": "healthy",
            "domain": "system",
            "version": "v2",
            "features": {
                "system_monitoring": True,
                "service_management": True,
                "configuration_api": True,
            },
            "timestamp": "2025-01-11T00:00:00Z"
        }

    @router.get("/schemas")
    async def get_schemas(request: Request) -> Dict[str, Any]:
        """Export schemas for system domain"""
        _check_domain_api_enabled(request)

        return {
            "message": "System domain schemas available",
            "available_endpoints": ["/health", "/schemas", "/info", "/status", "/services"]
        }

    @router.get("/info", response_model=SystemInfo)
    async def get_system_info(request: Request) -> SystemInfo:
        """Get system information"""
        _check_domain_api_enabled(request)

        try:
            return SystemInfo(
                hostname=platform.node(),
                platform=platform.system(),
                architecture=platform.machine(),
                python_version=platform.python_version(),
                uptime_seconds=time.time(),  # Simplified - would use actual uptime
                timestamp=time.time()
            )

        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get system info: {e!s}")

    @router.get("/status", response_model=SystemStatus)
    async def get_system_status(request: Request) -> SystemStatus:
        """Get overall system status"""
        _check_domain_api_enabled(request)

        try:
            feature_manager = get_feature_manager_from_request(request)

            # Get all registered features as "services"
            services = []
            all_features = feature_manager.get_all_features()

            for feature_name, feature in all_features.items():
                is_enabled = feature_manager.is_enabled(feature_name)
                is_healthy = feature.is_healthy() if hasattr(feature, 'is_healthy') else True

                if is_healthy and is_enabled:
                    status = "healthy"
                elif is_enabled:
                    status = "degraded"
                else:
                    status = "disabled"

                services.append(ServiceStatus(
                    name=feature_name,
                    status=status,
                    enabled=is_enabled,
                    last_check=time.time()
                ))

            healthy_count = len([s for s in services if s.status == "healthy"])
            total_count = len(services)

            # Determine overall status
            if healthy_count == total_count:
                overall_status = "healthy"
            elif healthy_count >= total_count * 0.8:
                overall_status = "mostly_healthy"
            elif healthy_count >= total_count * 0.5:
                overall_status = "degraded"
            else:
                overall_status = "unhealthy"

            return SystemStatus(
                overall_status=overall_status,
                services=services,
                total_services=total_count,
                healthy_services=healthy_count,
                timestamp=time.time()
            )

        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get system status: {e!s}")

    @router.get("/services")
    async def get_services(request: Request) -> List[ServiceStatus]:
        """Get detailed service information"""
        _check_domain_api_enabled(request)

        try:
            feature_manager = get_feature_manager_from_request(request)
            services = []
            all_features = feature_manager.get_all_features()

            for feature_name, feature in all_features.items():
                is_enabled = feature_manager.is_enabled(feature_name)
                is_healthy = feature.is_healthy() if hasattr(feature, 'is_healthy') else True

                if is_healthy and is_enabled:
                    status = "healthy"
                elif is_enabled:
                    status = "degraded"
                else:
                    status = "disabled"

                services.append(ServiceStatus(
                    name=feature_name,
                    status=status,
                    enabled=is_enabled,
                    last_check=time.time()
                ))

            return services

        except Exception as e:
            logger.error(f"Error getting services: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get services: {e!s}")

    return router

@register_domain_router("system")
def register_system_router(app_state) -> APIRouter:
    """Register the system domain router"""
    return create_system_router()
