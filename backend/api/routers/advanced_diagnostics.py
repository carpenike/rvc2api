"""
Advanced Diagnostics API Routes

REST API endpoints for advanced diagnostic capabilities including
fault correlation, predictive maintenance, and system health monitoring.
"""

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from backend.services.feature_manager import get_feature_manager

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models


class DTCRequest(BaseModel):
    """Request model for submitting a DTC."""

    protocol: str = Field(..., description="Protocol name (rvc, j1939, firefly, spartan_k2)")
    code: int = Field(..., description="DTC code number")
    system_type: str = Field(..., description="Affected system type")
    source_address: int = Field(default=0, description="CAN source address")
    pgn: int | None = Field(default=None, description="J1939 PGN (if applicable)")
    dgn: int | None = Field(default=None, description="RV-C DGN (if applicable)")
    severity: str | None = Field(
        default=None, description="Override severity (critical, high, medium, low, info)"
    )
    description: str = Field(default="", description="Human-readable description")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class PerformanceDataRequest(BaseModel):
    """Request model for recording performance data."""

    system_type: str = Field(..., description="System type being measured")
    component_name: str = Field(..., description="Specific component name")
    metrics: dict[str, float] = Field(..., description="Performance metrics")
    timestamp: float | None = Field(default=None, description="Optional timestamp")


class DTCResolveRequest(BaseModel):
    """Request model for resolving a DTC."""

    protocol: str = Field(..., description="Protocol name")
    code: int = Field(..., description="DTC code number")
    source_address: int = Field(default=0, description="CAN source address")


class SystemHealthResponse(BaseModel):
    """Response model for system health."""

    system_type: str
    health_score: float
    status: str
    active_dtcs: int
    last_assessment: float


class DiagnosticStatusResponse(BaseModel):
    """Response model for diagnostic status."""

    enabled: bool
    healthy: bool
    active_dtcs: int
    historical_dtcs: int
    correlations_cached: int
    processing_stats: dict[str, Any]


# Dependency Functions


async def get_diagnostics_feature():
    """Get the advanced diagnostics feature instance."""
    feature_manager = get_feature_manager()
    feature = feature_manager.get_feature("advanced_diagnostics")

    if not feature:
        raise HTTPException(status_code=503, detail="Advanced diagnostics feature not available")

    if not feature.is_healthy():
        raise HTTPException(status_code=503, detail="Advanced diagnostics feature not healthy")

    return feature


# API Endpoints


@router.get("/status", response_model=dict[str, Any])
async def get_diagnostics_status(
    feature: Annotated[Any, Depends(get_diagnostics_feature)],
) -> dict[str, Any]:
    """
    Get comprehensive advanced diagnostics status.

    Returns:
        Detailed status information including configuration, statistics, and health
    """
    try:
        return feature.get_status()
    except Exception as e:
        logger.error(f"Error getting diagnostics status: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/dtc", response_model=dict[str, Any])
async def submit_dtc(
    dtc_request: DTCRequest, feature: Annotated[Any, Depends(get_diagnostics_feature)]
) -> dict[str, Any]:
    """
    Submit a diagnostic trouble code for processing.

    Args:
        dtc_request: DTC information

    Returns:
        Processed DTC information
    """
    try:
        result = feature.process_protocol_dtc(
            protocol=dtc_request.protocol,
            code=dtc_request.code,
            system_type=dtc_request.system_type,
            source_address=dtc_request.source_address,
            pgn=dtc_request.pgn,
            dgn=dtc_request.dgn,
            severity=dtc_request.severity,
            description=dtc_request.description,
            metadata=dtc_request.metadata,
        )

        if result is None:
            raise HTTPException(status_code=400, detail="Failed to process DTC")

        return result

    except Exception as e:
        logger.error(f"Error submitting DTC: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/dtc", response_model=dict[str, bool])
async def resolve_dtc(
    resolve_request: DTCResolveRequest, feature: Annotated[Any, Depends(get_diagnostics_feature)]
) -> dict[str, bool]:
    """
    Mark a diagnostic trouble code as resolved.

    Args:
        resolve_request: DTC resolution information

    Returns:
        Success status
    """
    try:
        success = feature.resolve_dtc(
            protocol=resolve_request.protocol,
            code=resolve_request.code,
            source_address=resolve_request.source_address,
        )

        return {"resolved": success}

    except Exception as e:
        logger.error(f"Error resolving DTC: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/dtcs", response_model=list[dict[str, Any]])
async def get_active_dtcs(
    feature: Annotated[Any, Depends(get_diagnostics_feature)],
    system_type: str | None = Query(None, description="Filter by system type"),
    severity: str | None = Query(None, description="Filter by severity level"),
    protocol: str | None = Query(None, description="Filter by protocol"),
) -> list[dict[str, Any]]:
    """
    Get active diagnostic trouble codes with optional filtering.

    Args:
        system_type: Filter by system type
        severity: Filter by severity level
        protocol: Filter by protocol

    Returns:
        List of active DTCs
    """
    try:
        # Get DTCs through the feature's handler
        if hasattr(feature, "handler") and feature.handler:
            dtcs = feature.handler.get_active_dtcs(
                system_type=feature._parse_system_type(system_type) if system_type else None,
                severity=feature._parse_severity(severity) if severity else None,
                protocol=feature._parse_protocol(protocol) if protocol else None,
            )
            return [dtc.to_dict() for dtc in dtcs]
        else:
            return []

    except Exception as e:
        logger.error(f"Error getting active DTCs: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/performance", response_model=dict[str, bool])
async def record_performance_data(
    performance_request: PerformanceDataRequest,
    feature: Annotated[Any, Depends(get_diagnostics_feature)],
) -> dict[str, bool]:
    """
    Record performance data for predictive analysis.

    Args:
        performance_request: Performance data

    Returns:
        Success status
    """
    try:
        success = feature.record_performance_data(
            system_type=performance_request.system_type,
            component_name=performance_request.component_name,
            metrics=performance_request.metrics,
            timestamp=performance_request.timestamp,
        )

        return {"recorded": success}

    except Exception as e:
        logger.error(f"Error recording performance data: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/health", response_model=dict[str, Any])
async def get_system_health(
    feature: Annotated[Any, Depends(get_diagnostics_feature)],
    system_type: str | None = Query(None, description="Specific system to query"),
) -> dict[str, Any]:
    """
    Get system health status.

    Args:
        system_type: Specific system to query, or None for all systems

    Returns:
        System health information
    """
    try:
        return feature.get_system_health(system_type)

    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/predictions", response_model=list[dict[str, Any]])
async def get_maintenance_predictions(
    feature: Annotated[Any, Depends(get_diagnostics_feature)],
    time_horizon_days: int = Query(
        default=90, description="Planning horizon in days", ge=1, le=365
    ),
) -> list[dict[str, Any]]:
    """
    Get maintenance predictions for the specified time horizon.

    Args:
        time_horizon_days: Planning horizon in days

    Returns:
        List of maintenance predictions
    """
    try:
        return feature.get_maintenance_predictions(time_horizon_days)

    except Exception as e:
        logger.error(f"Error getting maintenance predictions: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/correlations", response_model=list[dict[str, Any]])
async def get_fault_correlations(
    feature: Annotated[Any, Depends(get_diagnostics_feature)],
    time_window_seconds: float | None = Query(
        None, description="Time window for correlation analysis (seconds)", ge=1.0, le=3600.0
    ),
) -> list[dict[str, Any]]:
    """
    Get fault correlations within the specified time window.

    Args:
        time_window_seconds: Time window for correlation analysis

    Returns:
        List of fault correlations
    """
    try:
        return feature.get_fault_correlations(time_window_seconds)

    except Exception as e:
        logger.error(f"Error getting fault correlations: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/statistics", response_model=dict[str, Any])
async def get_diagnostic_statistics(
    feature: Annotated[Any, Depends(get_diagnostics_feature)],
) -> dict[str, Any]:
    """
    Get comprehensive diagnostic processing statistics.

    Returns:
        Diagnostic statistics and metrics
    """
    try:
        stats = {}

        if hasattr(feature, "handler") and feature.handler:
            stats["diagnostics"] = feature.handler.get_diagnostic_statistics()

        if hasattr(feature, "predictive_engine") and feature.predictive_engine:
            stats["predictive"] = feature.predictive_engine.get_prediction_statistics()

        return stats

    except Exception as e:
        logger.error(f"Error getting diagnostic statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e
