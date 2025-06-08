"""
Performance Analytics API Routes

REST API endpoints for performance analytics including telemetry collection,
benchmarking, trend analysis, and optimization recommendations.
"""

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from backend.services.feature_manager import get_feature_manager

logger = logging.getLogger(__name__)

router = APIRouter()


# Request/Response Models


class TelemetryRequest(BaseModel):
    """Request model for recording telemetry data."""

    protocol: str = Field(..., description="Protocol name (rvc, j1939, firefly, spartan_k2)")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")
    message_size: int = Field(default=0, description="Message size in bytes")
    interface: str | None = Field(default=None, description="CAN interface name")


class APIPerformanceRequest(BaseModel):
    """Request model for recording API performance."""

    endpoint: str = Field(..., description="API endpoint")
    response_time_ms: float = Field(..., description="Response time in milliseconds")
    status_code: int = Field(default=200, description="HTTP status code")


class WebSocketLatencyRequest(BaseModel):
    """Request model for recording WebSocket latency."""

    latency_ms: float = Field(..., description="WebSocket latency in milliseconds")
    connection_id: str | None = Field(default=None, description="Connection identifier")


class CANInterfaceLoadRequest(BaseModel):
    """Request model for recording CAN interface load."""

    interface: str = Field(..., description="CAN interface name")
    load_percent: float = Field(..., description="Bus load percentage", ge=0.0, le=100.0)
    message_rate: float = Field(..., description="Messages per second", ge=0.0)


class PerformanceReportRequest(BaseModel):
    """Request model for generating performance reports."""

    time_window_seconds: float = Field(
        default=3600.0, description="Time window for report (seconds)", ge=60.0, le=86400.0
    )


# Dependency Functions


async def get_performance_analytics_feature():
    """Get the performance analytics feature instance."""
    feature_manager = get_feature_manager()
    feature = feature_manager.get_feature("performance_analytics")

    if not feature:
        raise HTTPException(status_code=503, detail="Performance analytics feature not available")

    if not feature.is_healthy():
        raise HTTPException(status_code=503, detail="Performance analytics feature not healthy")

    return feature


# API Endpoints


@router.get("/status", response_model=dict[str, Any])
async def get_performance_analytics_status(
    feature: Annotated[Any, Depends(get_performance_analytics_feature)],
) -> dict[str, Any]:
    """
    Get comprehensive performance analytics status.

    Returns:
        Detailed status including configuration, statistics, and component health
    """
    try:
        return feature.get_status()
    except Exception as e:
        logger.error(f"Error getting performance analytics status: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/telemetry/protocol", response_model=dict[str, bool])
async def record_protocol_telemetry(
    telemetry_request: TelemetryRequest,
    feature: Annotated[Any, Depends(get_performance_analytics_feature)],
) -> dict[str, bool]:
    """
    Record protocol message processing performance data.

    Args:
        telemetry_request: Protocol telemetry data

    Returns:
        Success status
    """
    try:
        feature.record_protocol_message(
            protocol=telemetry_request.protocol,
            processing_time_ms=telemetry_request.processing_time_ms,
            message_size=telemetry_request.message_size,
            interface=telemetry_request.interface,
        )

        return {"recorded": True}

    except Exception as e:
        logger.error(f"Error recording protocol telemetry: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/telemetry/api", response_model=dict[str, bool])
async def record_api_performance(
    api_request: APIPerformanceRequest,
    feature: Annotated[Any, Depends(get_performance_analytics_feature)],
) -> dict[str, bool]:
    """
    Record API request performance data.

    Args:
        api_request: API performance data

    Returns:
        Success status
    """
    try:
        feature.record_api_request(
            endpoint=api_request.endpoint,
            response_time_ms=api_request.response_time_ms,
            status_code=api_request.status_code,
        )

        return {"recorded": True}

    except Exception as e:
        logger.error(f"Error recording API performance: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/telemetry/websocket", response_model=dict[str, bool])
async def record_websocket_latency(
    websocket_request: WebSocketLatencyRequest,
    feature: Annotated[Any, Depends(get_performance_analytics_feature)],
) -> dict[str, bool]:
    """
    Record WebSocket latency data.

    Args:
        websocket_request: WebSocket latency data

    Returns:
        Success status
    """
    try:
        feature.record_websocket_latency(
            latency_ms=websocket_request.latency_ms, connection_id=websocket_request.connection_id
        )

        return {"recorded": True}

    except Exception as e:
        logger.error(f"Error recording WebSocket latency: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/telemetry/can-interface", response_model=dict[str, bool])
async def record_can_interface_load(
    can_request: CANInterfaceLoadRequest,
    feature: Annotated[Any, Depends(get_performance_analytics_feature)],
) -> dict[str, bool]:
    """
    Record CAN interface load and performance data.

    Args:
        can_request: CAN interface performance data

    Returns:
        Success status
    """
    try:
        feature.record_can_interface_load(
            interface=can_request.interface,
            load_percent=can_request.load_percent,
            message_rate=can_request.message_rate,
        )

        return {"recorded": True}

    except Exception as e:
        logger.error(f"Error recording CAN interface load: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/metrics", response_model=list[dict[str, Any]])
async def get_performance_metrics(
    feature: Annotated[Any, Depends(get_performance_analytics_feature)],
    metric_type: str | None = Query(None, description="Specific metric type to retrieve"),
    time_window_seconds: float = Query(
        default=60.0, description="Time window for metrics", ge=1.0, le=86400.0
    ),
) -> list[dict[str, Any]]:
    """
    Get current performance metrics with optional filtering.

    Args:
        metric_type: Specific metric type to retrieve
        time_window_seconds: Time window for metrics

    Returns:
        List of performance metrics
    """
    try:
        return feature.get_current_metrics(metric_type, time_window_seconds)

    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/resource-utilization", response_model=dict[str, Any])
async def get_resource_utilization(
    feature: Annotated[Any, Depends(get_performance_analytics_feature)],
) -> dict[str, Any]:
    """
    Get current system resource utilization.

    Returns:
        Resource utilization data for CPU, memory, network, and CAN interfaces
    """
    try:
        return feature.get_resource_utilization()

    except Exception as e:
        logger.error(f"Error getting resource utilization: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/trends", response_model=dict[str, Any])
async def get_performance_trends(
    feature: Annotated[Any, Depends(get_performance_analytics_feature)],
    metric_type: str | None = Query(None, description="Specific metric type for trends"),
) -> dict[str, Any]:
    """
    Get performance trend analysis.

    Args:
        metric_type: Specific metric type or None for all trends

    Returns:
        Performance trend analysis data
    """
    try:
        return feature.get_performance_trends(metric_type)

    except Exception as e:
        logger.error(f"Error getting performance trends: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/baseline-deviations", response_model=list[dict[str, Any]])
async def get_baseline_deviations(
    feature: Annotated[Any, Depends(get_performance_analytics_feature)],
    time_window_seconds: float = Query(
        default=3600.0, description="Time window for deviations", ge=60.0, le=86400.0
    ),
) -> list[dict[str, Any]]:
    """
    Get performance baseline deviations.

    Args:
        time_window_seconds: Time window for deviation analysis

    Returns:
        List of baseline deviation alerts
    """
    try:
        return feature.get_baseline_deviations(time_window_seconds)

    except Exception as e:
        logger.error(f"Error getting baseline deviations: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/optimization-recommendations", response_model=list[dict[str, Any]])
async def get_optimization_recommendations(
    feature: Annotated[Any, Depends(get_performance_analytics_feature)],
) -> list[dict[str, Any]]:
    """
    Get automated optimization recommendations.

    Returns:
        List of optimization recommendations with implementation details
    """
    try:
        return feature.get_optimization_recommendations()

    except Exception as e:
        logger.error(f"Error getting optimization recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/report", response_model=dict[str, Any])
async def generate_performance_report(
    report_request: PerformanceReportRequest,
    feature: Annotated[Any, Depends(get_performance_analytics_feature)],
) -> dict[str, Any]:
    """
    Generate comprehensive performance analysis report.

    Args:
        report_request: Report generation parameters

    Returns:
        Comprehensive performance report including metrics, trends, and recommendations
    """
    try:
        return feature.generate_performance_report(report_request.time_window_seconds)

    except Exception as e:
        logger.error(f"Error generating performance report: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/protocol-throughput", response_model=dict[str, float])
async def get_protocol_throughput(
    feature: Annotated[Any, Depends(get_performance_analytics_feature)],
) -> dict[str, float]:
    """
    Get current protocol throughput metrics.

    Returns:
        Dictionary of protocol names to messages per second
    """
    try:
        if hasattr(feature, "telemetry_collector") and feature.telemetry_collector:
            return feature.telemetry_collector.get_protocol_throughput()
        else:
            return {}

    except Exception as e:
        logger.error(f"Error getting protocol throughput: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/statistics", response_model=dict[str, Any])
async def get_analytics_statistics(
    feature: Annotated[Any, Depends(get_performance_analytics_feature)],
) -> dict[str, Any]:
    """
    Get comprehensive performance analytics statistics.

    Returns:
        Statistics from all analytics components including telemetry, benchmarking, trends, and optimization
    """
    try:
        stats = {}

        # Get feature-level statistics
        feature_status = feature.get_status()
        stats["feature"] = feature_status.get("statistics", {})

        # Get component-specific statistics
        if "telemetry_statistics" in feature_status:
            stats["telemetry"] = feature_status["telemetry_statistics"]

        if "benchmark_statistics" in feature_status:
            stats["benchmarking"] = feature_status["benchmark_statistics"]

        if "trend_statistics" in feature_status:
            stats["trends"] = feature_status["trend_statistics"]

        if "optimization_statistics" in feature_status:
            stats["optimization"] = feature_status["optimization_statistics"]

        return stats

    except Exception as e:
        logger.error(f"Error getting analytics statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/reset-baselines", response_model=dict[str, bool])
async def reset_performance_baselines(
    feature: Annotated[Any, Depends(get_performance_analytics_feature)],
) -> dict[str, bool]:
    """
    Reset all performance baselines (admin operation).

    Returns:
        Success status
    """
    try:
        # This would reset baselines in the benchmarking engine
        # Implementation depends on specific requirements
        logger.info("Performance baselines reset requested")
        return {"reset": True}

    except Exception as e:
        logger.error(f"Error resetting performance baselines: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e
