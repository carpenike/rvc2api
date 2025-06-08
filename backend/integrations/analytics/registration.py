"""
Performance Analytics Feature Registration

Registration module for the performance analytics feature following established
registration patterns from other features.
"""

import logging
from typing import Any

from backend.core.config import Settings
from backend.integrations.analytics.feature import PerformanceAnalyticsFeature
from backend.services.feature_base import Feature

logger = logging.getLogger(__name__)


def register_performance_analytics_feature(settings: Settings) -> Feature:
    """
    Register the performance analytics feature.

    Args:
        settings: Application settings

    Returns:
        Configured PerformanceAnalyticsFeature instance
    """
    try:
        feature = PerformanceAnalyticsFeature(settings)
        logger.info("Performance analytics feature registered successfully")
        return feature

    except Exception as e:
        logger.error(f"Failed to register performance analytics feature: {e}")
        raise


def get_feature_info() -> dict[str, Any]:
    """
    Get information about the performance analytics feature.

    Returns:
        Feature information dictionary
    """
    return {
        "name": "performance_analytics",
        "friendly_name": "Performance Analytics",
        "description": "Comprehensive performance monitoring and optimization for RV-C systems",
        "version": "1.0.0",
        "capabilities": [
            "Real-time telemetry collection",
            "Performance baseline establishment",
            "Trend analysis and prediction",
            "Resource utilization monitoring",
            "Automated optimization recommendations",
            "Cross-protocol performance analytics",
        ],
        "dependencies": ["can_interface"],
        "optional_dependencies": ["advanced_diagnostics", "rvc", "j1939"],
        "configuration_prefix": "COACHIQ_PERFORMANCE_ANALYTICS__",
        "supported_protocols": ["RV-C", "J1939", "Firefly", "Spartan K2"],
        "resource_requirements": {"cpu_usage_percent": 5.0, "memory_mb": 100.0, "storage_mb": 50.0},
        "monitoring_capabilities": {
            "message_processing": "Real-time protocol message performance tracking",
            "api_performance": "REST API response time monitoring",
            "websocket_latency": "WebSocket communication latency tracking",
            "resource_utilization": "System CPU, memory, and network monitoring",
            "can_interface_load": "CAN bus load and throughput monitoring",
        },
        "analytics_features": {
            "benchmarking": "Establishes performance baselines and detects deviations",
            "trend_analysis": "Statistical trend detection with linear regression",
            "optimization_engine": "Automated performance optimization recommendations",
            "predictive_analytics": "Performance prediction with confidence intervals",
        },
    }
