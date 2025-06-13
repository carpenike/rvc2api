"""
Performance Metrics API Router

Provides REST endpoints for accessing CAN bus decoder performance metrics,
including Prometheus exposition format endpoints and performance summaries.

This module supports Phase 3.2 of the CAN Bus Decoder architecture improvements.
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import PlainTextResponse

logger = logging.getLogger(__name__)

# Global performance monitor instance (initialized by feature manager)
_performance_monitor = None


def set_performance_monitor(monitor) -> None:
    """Set the global performance monitor instance."""
    global _performance_monitor
    _performance_monitor = monitor


def get_performance_monitor():
    """Get the global performance monitor instance."""
    return _performance_monitor


def create_performance_metrics_router() -> APIRouter:
    """Create and configure the performance metrics router."""
    router = APIRouter(prefix="/performance", tags=["Performance Metrics"])

    @router.get(
        "/metrics",
        response_class=PlainTextResponse,
        summary="Prometheus Metrics",
        description="Get performance metrics in Prometheus exposition format",
    )
    async def get_prometheus_metrics():
        """Get performance metrics in Prometheus exposition format."""
        monitor = get_performance_monitor()
        if not monitor:
            raise HTTPException(status_code=503, detail="Performance monitoring not available")

        try:
            metrics = monitor.get_prometheus_metrics()
            return Response(content=metrics, media_type="text/plain; charset=utf-8")
        except Exception as e:
            logger.error("Error generating Prometheus metrics: %s", e)
            raise HTTPException(status_code=500, detail="Failed to generate metrics") from e

    @router.get(
        "/summary",
        response_model=dict[str, Any],
        summary="Performance Summary",
        description="Get comprehensive performance summary with statistics",
    )
    async def get_performance_summary():
        """Get comprehensive performance summary."""
        monitor = get_performance_monitor()
        if not monitor:
            raise HTTPException(status_code=503, detail="Performance monitoring not available")

        try:
            return monitor.get_performance_summary()
        except Exception as e:
            logger.error("Error generating performance summary: %s", e)
            raise HTTPException(
                status_code=500, detail="Failed to generate performance summary"
            ) from e

    @router.get(
        "/thresholds",
        response_model=list[dict[str, Any]],
        summary="Threshold Violations",
        description="Get current performance threshold violations",
    )
    async def get_threshold_violations():
        """Get current performance threshold violations."""
        monitor = get_performance_monitor()
        if not monitor:
            raise HTTPException(status_code=503, detail="Performance monitoring not available")

        try:
            return monitor.check_performance_thresholds()
        except Exception as e:
            logger.error("Error checking thresholds: %s", e)
            raise HTTPException(status_code=500, detail="Failed to check thresholds") from e

    @router.post(
        "/reset", summary="Reset Metrics", description="Reset all performance metrics (for testing)"
    )
    async def reset_metrics():
        """Reset all performance metrics."""
        monitor = get_performance_monitor()
        if not monitor:
            raise HTTPException(status_code=503, detail="Performance monitoring not available")

        try:
            monitor.reset_metrics()
            return {"message": "Metrics reset successfully"}
        except Exception as e:
            logger.error("Error resetting metrics: %s", e)
            raise HTTPException(status_code=500, detail="Failed to reset metrics") from e

    return router
