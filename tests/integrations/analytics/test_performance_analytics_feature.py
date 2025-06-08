"""
Performance Analytics Feature Tests

Comprehensive tests for the performance analytics feature including all components
and integration scenarios.
"""

import asyncio

import pytest

from backend.core.config import Settings
from backend.integrations.analytics.config import PerformanceAnalyticsSettings
from backend.integrations.analytics.feature import PerformanceAnalyticsFeature


@pytest.fixture
def performance_analytics_settings():
    """Create performance analytics settings for testing."""
    return PerformanceAnalyticsSettings(
        enabled=True,
        enable_telemetry_collection=True,
        enable_benchmarking=True,
        enable_trend_analysis=True,
        enable_optimization_recommendations=True,
        telemetry_collection_interval_seconds=1.0,
        resource_monitoring_interval_seconds=2.0,
        baseline_establishment_hours=1,
        trend_analysis_window_hours=1,
        minimum_trend_samples=5,
    )


@pytest.fixture
def settings_with_analytics(performance_analytics_settings):
    """Create settings with performance analytics configuration."""
    settings = Settings()
    settings.performance_analytics = performance_analytics_settings
    return settings


@pytest.fixture
def performance_analytics_feature(settings_with_analytics):
    """Create performance analytics feature for testing."""
    return PerformanceAnalyticsFeature(settings_with_analytics)


@pytest.mark.asyncio
class TestPerformanceAnalyticsFeature:
    """Test cases for PerformanceAnalyticsFeature."""

    async def test_feature_initialization(self, performance_analytics_feature):
        """Test feature initialization."""
        assert performance_analytics_feature.analytics_settings.enabled
        assert performance_analytics_feature.telemetry_collector is None  # Not started yet
        assert performance_analytics_feature.benchmarking_engine is None
        assert performance_analytics_feature.trend_analyzer is None
        assert performance_analytics_feature.optimization_engine is None

    async def test_feature_startup_enabled(self, performance_analytics_feature):
        """Test feature startup when enabled."""
        await performance_analytics_feature.startup()

        # Verify all components are initialized
        assert performance_analytics_feature.telemetry_collector is not None
        assert performance_analytics_feature.benchmarking_engine is not None
        assert performance_analytics_feature.trend_analyzer is not None
        assert performance_analytics_feature.optimization_engine is not None

        # Verify feature is healthy
        assert performance_analytics_feature.is_healthy()
        assert performance_analytics_feature.health == "healthy"

        # Cleanup
        await performance_analytics_feature.shutdown()

    async def test_feature_startup_disabled(self, settings_with_analytics):
        """Test feature startup when disabled."""
        settings_with_analytics.performance_analytics.enabled = False
        feature = PerformanceAnalyticsFeature(settings_with_analytics)

        await feature.startup()

        # Verify components are not initialized
        assert feature.telemetry_collector is None
        assert feature.benchmarking_engine is None
        assert feature.trend_analyzer is None
        assert feature.optimization_engine is None

        # Verify feature health
        assert feature.is_healthy()  # Should be healthy when disabled
        assert feature.health == "disabled"

    async def test_feature_shutdown(self, performance_analytics_feature):
        """Test feature shutdown."""
        await performance_analytics_feature.startup()

        # Verify components are initialized
        assert performance_analytics_feature.is_healthy()

        await performance_analytics_feature.shutdown()

        # Verify components are cleaned up
        assert performance_analytics_feature.telemetry_collector is None
        assert performance_analytics_feature.benchmarking_engine is None
        assert performance_analytics_feature.trend_analyzer is None
        assert performance_analytics_feature.optimization_engine is None

    async def test_get_status(self, performance_analytics_feature):
        """Test status reporting."""
        await performance_analytics_feature.startup()

        status = performance_analytics_feature.get_status()

        # Verify status structure
        assert "enabled" in status
        assert "healthy" in status
        assert "current_performance_status" in status
        assert "components" in status
        assert "configuration" in status
        assert "statistics" in status

        # Verify component status
        assert status["components"]["telemetry_collector"]
        assert status["components"]["benchmarking_engine"]
        assert status["components"]["trend_analyzer"]
        assert status["components"]["optimization_engine"]

        # Verify configuration
        assert status["configuration"]["telemetry_collection"]
        assert status["configuration"]["benchmarking"]
        assert status["configuration"]["trend_analysis"]
        assert status["configuration"]["optimization_recommendations"]

        await performance_analytics_feature.shutdown()

    async def test_record_protocol_message(self, performance_analytics_feature):
        """Test protocol message recording."""
        await performance_analytics_feature.startup()

        # Record a protocol message
        performance_analytics_feature.record_protocol_message(
            protocol="rvc", processing_time_ms=1.5, message_size=8, interface="can0"
        )

        # Verify metric was recorded
        assert performance_analytics_feature._stats["metrics_collected"] == 1

        await performance_analytics_feature.shutdown()

    async def test_record_api_request(self, performance_analytics_feature):
        """Test API request recording."""
        await performance_analytics_feature.startup()

        # Record an API request
        performance_analytics_feature.record_api_request(
            endpoint="/api/entities", response_time_ms=25.0, status_code=200
        )

        # Verify metric was recorded
        assert performance_analytics_feature._stats["metrics_collected"] == 1

        await performance_analytics_feature.shutdown()

    async def test_record_websocket_latency(self, performance_analytics_feature):
        """Test WebSocket latency recording."""
        await performance_analytics_feature.startup()

        # Record WebSocket latency
        performance_analytics_feature.record_websocket_latency(
            latency_ms=5.0, connection_id="conn-123"
        )

        # Verify metric was recorded
        assert performance_analytics_feature._stats["metrics_collected"] == 1

        await performance_analytics_feature.shutdown()

    async def test_record_can_interface_load(self, performance_analytics_feature):
        """Test CAN interface load recording."""
        await performance_analytics_feature.startup()

        # Record CAN interface load
        performance_analytics_feature.record_can_interface_load(
            interface="can0", load_percent=35.0, message_rate=450.0
        )

        # Verify metric was recorded
        assert performance_analytics_feature._stats["metrics_collected"] == 1

        await performance_analytics_feature.shutdown()

    async def test_get_current_metrics(self, performance_analytics_feature):
        """Test retrieving current metrics."""
        await performance_analytics_feature.startup()

        # Record some metrics
        performance_analytics_feature.record_protocol_message("rvc", 1.0)
        performance_analytics_feature.record_api_request("/test", 20.0)

        # Get current metrics
        metrics = performance_analytics_feature.get_current_metrics()

        # Verify metrics are returned (exact count depends on internal processing)
        assert isinstance(metrics, list)

        # Test with specific metric type
        api_metrics = performance_analytics_feature.get_current_metrics("api_response_time")
        assert isinstance(api_metrics, list)

        await performance_analytics_feature.shutdown()

    async def test_get_resource_utilization(self, performance_analytics_feature):
        """Test resource utilization retrieval."""
        await performance_analytics_feature.startup()

        # Get resource utilization
        utilization = performance_analytics_feature.get_resource_utilization()

        # Verify structure
        assert isinstance(utilization, dict)
        # Note: Actual content depends on psutil availability and system state

        await performance_analytics_feature.shutdown()

    async def test_get_performance_trends(self, performance_analytics_feature):
        """Test performance trends retrieval."""
        await performance_analytics_feature.startup()

        # Get performance trends
        trends = performance_analytics_feature.get_performance_trends()

        # Verify structure
        assert isinstance(trends, dict)

        # Test with specific metric type
        cpu_trends = performance_analytics_feature.get_performance_trends("cpu_usage")
        assert isinstance(cpu_trends, dict)

        await performance_analytics_feature.shutdown()

    async def test_get_baseline_deviations(self, performance_analytics_feature):
        """Test baseline deviations retrieval."""
        await performance_analytics_feature.startup()

        # Get baseline deviations
        deviations = performance_analytics_feature.get_baseline_deviations()

        # Verify structure
        assert isinstance(deviations, list)

        await performance_analytics_feature.shutdown()

    async def test_get_optimization_recommendations(self, performance_analytics_feature):
        """Test optimization recommendations retrieval."""
        await performance_analytics_feature.startup()

        # Get optimization recommendations
        recommendations = performance_analytics_feature.get_optimization_recommendations()

        # Verify structure
        assert isinstance(recommendations, list)

        # Verify stats are updated
        initial_count = performance_analytics_feature._stats["recommendations_generated"]

        # Get recommendations again
        performance_analytics_feature.get_optimization_recommendations()

        # Verify count increased (if recommendations were generated)
        final_count = performance_analytics_feature._stats["recommendations_generated"]
        assert final_count >= initial_count

        await performance_analytics_feature.shutdown()

    async def test_generate_performance_report(self, performance_analytics_feature):
        """Test performance report generation."""
        await performance_analytics_feature.startup()

        # Generate a performance report
        report = performance_analytics_feature.generate_performance_report(
            time_window_seconds=300.0
        )

        # Verify report structure
        assert "report_id" in report
        assert "generated_at" in report
        assert "time_window_seconds" in report
        assert "overall_status" in report
        assert "status_summary" in report
        assert "current_metrics" in report
        assert "resource_utilization" in report
        assert "performance_trends" in report
        assert "baseline_deviations" in report
        assert "optimization_recommendations" in report

        # Verify report ID is stored
        assert performance_analytics_feature._last_report_id == report["report_id"]

        # Verify stats are updated
        assert performance_analytics_feature._stats["reports_generated"] == 1

        await performance_analytics_feature.shutdown()

    async def test_error_handling(self, performance_analytics_feature):
        """Test error handling in various scenarios."""
        # Test recording methods when not started
        performance_analytics_feature.record_protocol_message("rvc", 1.0)
        performance_analytics_feature.record_api_request("/test", 20.0)
        performance_analytics_feature.record_websocket_latency(5.0)
        performance_analytics_feature.record_can_interface_load("can0", 35.0, 450.0)

        # Should not crash and should return empty/default values
        metrics = performance_analytics_feature.get_current_metrics()
        assert metrics == []

        utilization = performance_analytics_feature.get_resource_utilization()
        assert utilization == {}

        trends = performance_analytics_feature.get_performance_trends()
        assert trends == {}

        deviations = performance_analytics_feature.get_baseline_deviations()
        assert deviations == []

        recommendations = performance_analytics_feature.get_optimization_recommendations()
        assert recommendations == []

    async def test_invalid_metric_types(self, performance_analytics_feature):
        """Test handling of invalid metric types."""
        await performance_analytics_feature.startup()

        # Test with invalid metric type
        metrics = performance_analytics_feature.get_current_metrics("invalid_metric_type")
        assert metrics == []

        trends = performance_analytics_feature.get_performance_trends("invalid_metric_type")
        assert trends == {}

        await performance_analytics_feature.shutdown()

    @pytest.mark.slow
    async def test_background_task_integration(self, performance_analytics_feature):
        """Test background task integration (slow test)."""
        await performance_analytics_feature.startup()

        # Record some metrics to trigger background processing
        for i in range(10):
            performance_analytics_feature.record_protocol_message("rvc", 1.0 + i * 0.1)
            performance_analytics_feature.record_api_request("/test", 20.0 + i)
            await asyncio.sleep(0.1)

        # Wait for background processing
        await asyncio.sleep(2.0)

        # Verify background tasks are running
        assert len(performance_analytics_feature._background_tasks) > 0

        # Verify some background tasks are active
        active_tasks = [t for t in performance_analytics_feature._background_tasks if not t.done()]
        assert len(active_tasks) > 0

        await performance_analytics_feature.shutdown()


@pytest.mark.asyncio
class TestPerformanceAnalyticsIntegration:
    """Integration tests for performance analytics with other components."""

    async def test_feature_registration_info(self):
        """Test feature registration information."""
        from backend.integrations.analytics.registration import get_feature_info

        info = get_feature_info()

        # Verify basic info
        assert info["name"] == "performance_analytics"
        assert info["friendly_name"] == "Performance Analytics"
        assert "description" in info
        assert "capabilities" in info
        assert "dependencies" in info

        # Verify capabilities
        assert "Real-time telemetry collection" in info["capabilities"]
        assert "Performance baseline establishment" in info["capabilities"]
        assert "Trend analysis and prediction" in info["capabilities"]
        assert "Automated optimization recommendations" in info["capabilities"]

    async def test_settings_validation(self):
        """Test performance analytics settings validation."""
        # Test valid settings
        settings = PerformanceAnalyticsSettings(
            enabled=True,
            telemetry_collection_interval_seconds=5.0,
            cpu_warning_threshold_percent=80.0,
            memory_warning_threshold_percent=80.0,
        )

        assert settings.enabled
        assert settings.telemetry_collection_interval_seconds == 5.0
        assert settings.cpu_warning_threshold_percent == 80.0

        # Test boundary values
        settings = PerformanceAnalyticsSettings(
            telemetry_collection_interval_seconds=0.1,  # Minimum
            cpu_warning_threshold_percent=100.0,  # Maximum
            metric_retention_hours=168,  # Maximum
        )

        assert settings.telemetry_collection_interval_seconds == 0.1
        assert settings.cpu_warning_threshold_percent == 100.0
        assert settings.metric_retention_hours == 168

    async def test_environment_variable_integration(self):
        """Test environment variable integration."""
        import os

        # Set environment variables
        os.environ["COACHIQ_PERFORMANCE_ANALYTICS__ENABLED"] = "true"
        os.environ["COACHIQ_PERFORMANCE_ANALYTICS__TELEMETRY_COLLECTION_INTERVAL_SECONDS"] = "2.5"
        os.environ["COACHIQ_PERFORMANCE_ANALYTICS__CPU_WARNING_THRESHOLD_PERCENT"] = "75.0"

        try:
            # Create settings from environment
            settings = PerformanceAnalyticsSettings()

            # Verify environment variables were used
            assert settings.enabled
            assert settings.telemetry_collection_interval_seconds == 2.5
            assert settings.cpu_warning_threshold_percent == 75.0

        finally:
            # Clean up environment variables
            for key in list(os.environ.keys()):
                if key.startswith("COACHIQ_PERFORMANCE_ANALYTICS__"):
                    del os.environ[key]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
