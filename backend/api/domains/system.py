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
import os
import time
import platform
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from backend.core.dependencies import get_feature_manager_from_request
from backend.api.domains import register_domain_router

logger = logging.getLogger(__name__)


def _map_service_status_to_ietf(status: str) -> str:
    """Map internal service status values to IETF-compliant values."""
    status_mapping = {
        "healthy": "pass",
        "degraded": "warn",
        "failed": "fail",
        "disabled": "pass",  # Disabled services are not unhealthy
    }
    return status_mapping.get(status, status)


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


class ServiceMetadata(BaseModel):
    """Service metadata information"""

    name: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    environment: str = Field(..., description="Environment (development, staging, production)")
    hostname: str = Field(..., description="System hostname")
    platform: str = Field(..., description="Operating system platform")


class SystemStatus(BaseModel):
    """Overall system status with enhanced metadata"""

    overall_status: str = Field(..., description="Overall system status")
    services: list[ServiceStatus] = Field(..., description="Individual service statuses")
    total_services: int = Field(..., description="Total number of services")
    healthy_services: int = Field(..., description="Number of healthy services")
    timestamp: float = Field(..., description="Status timestamp")

    # Enhanced metadata from healthz
    response_time_ms: float | None = Field(None, description="Response time in milliseconds")
    service: ServiceMetadata | None = Field(None, description="Service metadata")
    description: str | None = Field(None, description="Human-readable status description")


def create_system_router() -> APIRouter:
    """Create the system domain router with all endpoints"""
    router = APIRouter(tags=["system-v2"])

    def _check_domain_api_enabled(request: Request) -> None:
        """Check if system API v2 is enabled"""
        feature_manager = get_feature_manager_from_request(request)
        if not feature_manager.is_enabled("domain_api_v2"):
            raise HTTPException(
                status_code=404,
                detail="Domain API v2 is disabled. Enable with COACHIQ_FEATURES__DOMAIN_API_V2=true",
            )
        # Note: system_api_v2 feature flag doesn't exist yet, so we skip that check

    @router.get("/health")
    async def health_check(request: Request) -> dict[str, Any]:
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
            "timestamp": "2025-01-11T00:00:00Z",
        }

    @router.get("/schemas")
    async def get_schemas(request: Request) -> dict[str, Any]:
        """Export schemas for system domain"""
        _check_domain_api_enabled(request)

        return {
            "message": "System domain schemas available",
            "available_endpoints": ["/health", "/schemas", "/info", "/status", "/services"],
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
                timestamp=time.time(),
            )

        except Exception as e:
            logger.error(f"Error getting system info: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get system info: {e!s}")

    @router.get("/status")
    async def get_system_status(request: Request, format: str = "default") -> dict[str, Any]:
        """Get overall system status with enhanced metadata

        Supports multiple formats:
        - default: Standard SystemStatus response
        - ietf: IETF health+json compliant format
        """
        _check_domain_api_enabled(request)

        start_time = time.time()

        try:
            feature_manager = get_feature_manager_from_request(request)

            # Get all registered features as "services"
            services = []
            all_features = feature_manager.get_all_features()

            failed_features = {}
            degraded_features = {}
            healthy_features = {}
            disabled_features = {}

            for feature_name, feature in all_features.items():
                is_enabled = feature_manager.is_enabled(feature_name)
                is_healthy = feature.is_healthy() if hasattr(feature, "is_healthy") else True

                if not is_enabled:
                    status = "disabled"
                    disabled_features[feature_name] = status
                elif is_healthy:
                    status = "healthy"
                    healthy_features[feature_name] = status
                else:
                    # Check if it's failed or just degraded
                    health_status = getattr(feature, "health", "degraded")
                    if health_status == "failed":
                        status = "failed"
                        failed_features[feature_name] = status
                    else:
                        status = "degraded"
                        degraded_features[feature_name] = status

                services.append(
                    ServiceStatus(
                        name=feature_name, status=status, enabled=is_enabled, last_check=time.time()
                    )
                )

            healthy_count = len([s for s in services if s.status == "healthy"])
            total_count = len([s for s in services if s.enabled])  # Only count enabled services

            # Determine overall status using safety-critical classification
            critical_failures = {}
            warning_failures = {}
            critical_degraded = {}
            warning_degraded = {}

            # Categorize failures based on safety classification (same logic as healthz)
            for feature_name in failed_features:
                safety_class = feature_manager.get_safety_classification(feature_name)
                if safety_class and safety_class.value in ["critical", "safety_related"]:
                    critical_failures[feature_name] = failed_features[feature_name]
                else:
                    warning_failures[feature_name] = failed_features[feature_name]

            for feature_name in degraded_features:
                safety_class = feature_manager.get_safety_classification(feature_name)
                if safety_class and safety_class.value in ["critical", "safety_related"]:
                    critical_degraded[feature_name] = degraded_features[feature_name]
                else:
                    warning_degraded[feature_name] = degraded_features[feature_name]

            # Overall status logic using same logic as healthz
            if critical_failures:
                overall_status = "failed"
                ietf_status = "fail"
            elif critical_degraded or warning_failures:
                overall_status = "degraded"
                ietf_status = "warn"
            elif warning_degraded:
                overall_status = "degraded"
                ietf_status = "warn"
            else:
                overall_status = "healthy"
                ietf_status = "pass"

            # Get service version (same logic as healthz)
            try:
                version_file = Path(__file__).parent.parent.parent / "VERSION"
                if version_file.exists():
                    version = version_file.read_text().strip()
                else:
                    version = os.getenv("VERSION", "development")
            except Exception:
                version = "unknown"

            # Calculate response time
            response_time_ms = round((time.time() - start_time) * 1000, 2)

            # Create service metadata
            service_metadata = ServiceMetadata(
                name="coachiq",
                version=version,
                environment=os.getenv("ENVIRONMENT", "development"),
                hostname=platform.node(),
                platform=platform.system(),
            )

            # Generate status description
            if failed_features:
                description = f"Service critical: {len(failed_features)} service(s) failed"
            elif degraded_features:
                description = f"Service degraded: {len(degraded_features)} service(s) degraded"
            else:
                description = "All services operational"

            # Return format based on request
            if format.lower() == "ietf":
                # IETF health+json format
                ietf_response = {
                    "status": ietf_status,
                    "version": "1",  # Health check format version
                    "releaseId": version,
                    "serviceId": "coachiq-system",
                    "description": description,
                    "timestamp": datetime.now(UTC).isoformat(),
                    "checks": {
                        service.name: {"status": _map_service_status_to_ietf(service.status)}
                        for service in services
                        if service.enabled
                    },
                    "service": {
                        "name": service_metadata.name,
                        "version": service_metadata.version,
                        "environment": service_metadata.environment,
                        "hostname": service_metadata.hostname,
                        "platform": service_metadata.platform,
                    },
                    "response_time_ms": response_time_ms,
                }

                # Add categorized issues for safety-aware orchestration
                if failed_features or degraded_features:
                    ietf_response["issues"] = {
                        "critical": {
                            "failed": list(critical_failures.keys()),
                            "degraded": list(critical_degraded.keys()),
                        },
                        "warning": {
                            "failed": list(warning_failures.keys()),
                            "degraded": list(warning_degraded.keys()),
                        },
                    }

                return ietf_response

            # Default SystemStatus format
            return SystemStatus(
                overall_status=overall_status,
                services=services,
                total_services=total_count,
                healthy_services=healthy_count,
                timestamp=time.time(),
                response_time_ms=response_time_ms,
                service=service_metadata,
                description=description,
            ).model_dump()

        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get system status: {e!s}")

    @router.get("/services")
    async def get_services(request: Request) -> list[ServiceStatus]:
        """Get detailed service information"""
        _check_domain_api_enabled(request)

        try:
            feature_manager = get_feature_manager_from_request(request)
            services = []
            all_features = feature_manager.get_all_features()

            for feature_name, feature in all_features.items():
                is_enabled = feature_manager.is_enabled(feature_name)
                is_healthy = feature.is_healthy() if hasattr(feature, "is_healthy") else True

                if is_healthy and is_enabled:
                    status = "healthy"
                elif is_enabled:
                    status = "degraded"
                else:
                    status = "disabled"

                services.append(
                    ServiceStatus(
                        name=feature_name, status=status, enabled=is_enabled, last_check=time.time()
                    )
                )

            return services

        except Exception as e:
            logger.error(f"Error getting services: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get services: {e!s}")

    return router


@register_domain_router("system")
def register_system_router(_app_state) -> APIRouter:
    """Register the system domain router"""
    return create_system_router()
