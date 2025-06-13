"""
API endpoints for CAN Bus Decoder V2 Migration Management.

Provides REST API for monitoring and controlling the migration from legacy
to V2 decoder architecture, including status monitoring, phase advancement,
and vehicle enrollment management.
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services.migration_service import get_migration_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/migration", tags=["migration"])


class VehicleEnrollmentRequest(BaseModel):
    """Request model for vehicle enrollment."""
    vehicle_id: str


class PhaseAdvancementResponse(BaseModel):
    """Response model for phase advancement."""
    success: bool
    message: str
    previous_phase: str | None = None
    new_phase: str | None = None


class VehicleEnrollmentResponse(BaseModel):
    """Response model for vehicle enrollment."""
    success: bool
    message: str
    vehicle_id: str
    phase: str | None = None


@router.get("/status")
async def get_migration_status() -> dict[str, Any]:
    """
    Get comprehensive migration status and metrics.

    Returns:
        Migration status including current phase, validation metrics,
        vehicle enrollments, and performance comparisons.
    """
    try:
        migration_service = get_migration_service()
        status = migration_service.get_migration_status()

        return {
            "status": "success",
            "data": status,
        }

    except Exception as e:
        logger.error(f"Error getting migration status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get migration status: {str(e)}"
        )


@router.post("/advance", response_model=PhaseAdvancementResponse)
async def advance_migration_phase() -> PhaseAdvancementResponse:
    """
    Manually advance migration to the next phase if conditions are met.

    Phases:
    - disabled -> validation (parallel processing)
    - validation -> limited_rollout (test vehicles)
    - limited_rollout -> production_rollout (production vehicles)
    - production_rollout -> complete (legacy decommissioned)

    Returns:
        Result of phase advancement attempt.
    """
    try:
        migration_service = get_migration_service()
        result = migration_service.advance_migration_phase()

        return PhaseAdvancementResponse(**result)

    except Exception as e:
        logger.error(f"Error advancing migration phase: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to advance migration phase: {str(e)}"
        )


@router.post("/vehicles/enroll", response_model=VehicleEnrollmentResponse)
async def enroll_vehicle(
    request: VehicleEnrollmentRequest
) -> VehicleEnrollmentResponse:
    """
    Enroll a vehicle to use V2 decoder architecture.

    Vehicle enrollment is only available during limited_rollout and
    production_rollout phases.

    Args:
        request: Vehicle enrollment request with vehicle ID

    Returns:
        Result of vehicle enrollment attempt.
    """
    try:
        migration_service = get_migration_service()
        result = migration_service.enroll_vehicle(request.vehicle_id)

        return VehicleEnrollmentResponse(**result)

    except Exception as e:
        logger.error(f"Error enrolling vehicle {request.vehicle_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to enroll vehicle: {str(e)}"
        )


@router.get("/vehicles")
async def get_enrolled_vehicles() -> dict[str, Any]:
    """
    Get list of all enrolled vehicles and their status.

    Returns:
        List of enrolled vehicles with enrollment details,
        error counts, and validation results.
    """
    try:
        migration_service = get_migration_service()
        status = migration_service.get_migration_status()

        return {
            "status": "success",
            "data": {
                "total_enrolled": status.get("vehicle_enrollment", {}).get("total_enrolled", 0),
                "by_phase": status.get("vehicle_enrollment", {}).get("by_phase", {}),
                "vehicles": status.get("vehicle_enrollment", {}).get("vehicles", {}),
            },
        }

    except Exception as e:
        logger.error(f"Error getting enrolled vehicles: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get enrolled vehicles: {str(e)}"
        )


@router.get("/metrics")
async def get_migration_metrics() -> dict[str, Any]:
    """
    Get detailed migration performance metrics.

    Returns:
        Performance comparison metrics, validation results,
        and system health indicators.
    """
    try:
        migration_service = get_migration_service()
        status = migration_service.get_migration_status()

        return {
            "status": "success",
            "data": {
                "validation_stats": status.get("validation_stats", {}),
                "performance_metrics": status.get("performance_metrics", {}),
                "can_advance": status.get("can_advance", {}),
                "uptime_hours": status.get("uptime_hours", 0),
            },
        }

    except Exception as e:
        logger.error(f"Error getting migration metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get migration metrics: {str(e)}"
        )


@router.get("/health")
async def get_migration_health() -> dict[str, Any]:
    """
    Get migration system health check.

    Returns:
        Health status including error rates, rollback events,
        and system stability indicators.
    """
    try:
        migration_service = get_migration_service()
        status = migration_service.get_migration_status()

        validation_stats = status.get("validation_stats", {})
        success_rate = validation_stats.get("success_rate", 0)
        rollback_events = validation_stats.get("rollback_events", 0)
        total_validations = validation_stats.get("total_validations", 0)

        # Determine overall health
        health_status = "healthy"
        if success_rate < 0.95:
            health_status = "degraded"
        if rollback_events > 0 or success_rate < 0.90:
            health_status = "unhealthy"
        if total_validations == 0:
            health_status = "unknown"

        health_data = {
            "overall_status": health_status,
            "success_rate": success_rate,
            "rollback_events": rollback_events,
            "total_validations": total_validations,
            "current_phase": status.get("current_phase", "unknown"),
            "enrolled_vehicles": status.get("vehicle_enrollment", {}).get("total_enrolled", 0),
            "uptime_hours": status.get("uptime_hours", 0),
        }

        return {
            "status": "success",
            "data": health_data,
        }

    except Exception as e:
        logger.error(f"Error getting migration health: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get migration health: {str(e)}"
        )


@router.get("/phases")
async def get_migration_phases() -> dict[str, Any]:
    """
    Get information about migration phases and advancement criteria.

    Returns:
        Description of migration phases, current phase,
        and criteria for advancing to next phase.
    """
    phases_info = {
        "disabled": {
            "description": "Migration disabled, legacy decoder only",
            "next_phase": "validation",
            "advancement_criteria": [
                "System health checks pass",
                "Safety engine in safe state",
                "Feature flag enabled"
            ]
        },
        "validation": {
            "description": "Parallel processing validation phase",
            "next_phase": "limited_rollout",
            "advancement_criteria": [
                "Minimum 1000 validations completed",
                "Success rate >= 99%",
                "Performance delta within acceptable range",
                "No safety event mismatches"
            ]
        },
        "limited_rollout": {
            "description": "V2 active for enrolled test vehicles",
            "next_phase": "production_rollout",
            "advancement_criteria": [
                "Minimum 5 vehicles successfully enrolled",
                "Vehicle success rate >= 95%",
                "No rollback events",
                "Sustained operation for test period"
            ]
        },
        "production_rollout": {
            "description": "V2 active for enrolled production vehicles",
            "next_phase": "complete",
            "advancement_criteria": [
                "Minimum 50 vehicles enrolled",
                "One week sustained operation",
                "Zero rollback events",
                "System stability confirmed"
            ]
        },
        "complete": {
            "description": "Migration complete, legacy decommissioned",
            "next_phase": None,
            "advancement_criteria": []
        }
    }

    try:
        migration_service = get_migration_service()
        status = migration_service.get_migration_status()
        current_phase = status.get("current_phase", "disabled")
        can_advance = status.get("can_advance", {})

        return {
            "status": "success",
            "data": {
                "phases": phases_info,
                "current_phase": current_phase,
                "can_advance": can_advance,
                "current_phase_info": phases_info.get(current_phase, {}),
            },
        }

    except Exception as e:
        logger.error(f"Error getting migration phases info: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get migration phases info: {str(e)}"
        )
