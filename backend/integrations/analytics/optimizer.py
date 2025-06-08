"""
Performance Optimization Engine

Automated generation of optimization recommendations based on performance analysis.
Provides actionable suggestions for improving system performance and resource utilization.
"""

import asyncio
import logging
from typing import Any

from backend.integrations.analytics.config import PerformanceAnalyticsSettings
from backend.integrations.analytics.models import (
    MetricType,
    OptimizationCategory,
    OptimizationRecommendation,
    PerformanceMetric,
    ResourceType,
    ResourceUtilization,
)

logger = logging.getLogger(__name__)


class OptimizationEngine:
    """
    Performance optimization engine for automated recommendation generation.

    Analyzes performance metrics, resource utilization, and trends to generate
    actionable optimization recommendations across configuration, resource
    allocation, architecture, and protocol-specific improvements.
    """

    def __init__(self, settings: PerformanceAnalyticsSettings):
        """Initialize the optimization engine."""
        self.settings = settings

        # Recommendation storage
        self._recommendations: dict[OptimizationCategory, list[OptimizationRecommendation]] = {
            category: [] for category in OptimizationCategory
        }

        # Analysis data
        self._current_metrics: dict[MetricType, PerformanceMetric] = {}
        self._resource_utilization: dict[ResourceType, ResourceUtilization] = {}
        self._performance_trends: dict[MetricType, Any] = {}  # TrendAnalyzer results

        # Background tasks
        self._optimization_tasks: list[asyncio.Task] = []
        self._running = False

        # Optimization statistics
        self._optimization_stats = {
            "recommendations_generated": 0,
            "optimization_cycles": 0,
            "recommendations_by_category": {cat.value: 0 for cat in OptimizationCategory},
            "high_priority_recommendations": 0,
        }

        # Optimization rules and thresholds
        self._optimization_rules = self._initialize_optimization_rules()

        logger.info("Optimization engine initialized")

    def _initialize_optimization_rules(self) -> dict[str, Any]:
        """Initialize optimization rules and thresholds."""
        return {
            # CPU optimization thresholds
            "cpu_high_usage_threshold": 80.0,
            "cpu_optimization_threshold": 70.0,
            # Memory optimization thresholds
            "memory_high_usage_threshold": 80.0,
            "memory_optimization_threshold": 70.0,
            # Message processing thresholds
            "low_throughput_threshold": 0.8,  # 80% of target
            "high_latency_threshold": 2.0,  # 2x target latency
            # CAN bus optimization thresholds
            "can_bus_high_load_threshold": 70.0,
            "can_bus_optimization_threshold": 60.0,
            # Trend analysis thresholds
            "degrading_trend_threshold": -0.1,  # 10% degradation per hour
            "volatile_trend_threshold": 0.3,  # 30% coefficient of variation
        }

    async def startup(self) -> None:
        """Start optimization engine tasks."""
        if not self.settings.enabled or not self.settings.enable_optimization_recommendations:
            logger.info("Optimization engine disabled")
            return

        self._running = True

        # Start optimization analysis task
        optimization_task = asyncio.create_task(self._optimization_analysis_loop())
        self._optimization_tasks.append(optimization_task)

        logger.info("Optimization engine started")

    async def shutdown(self) -> None:
        """Shutdown optimization engine."""
        self._running = False

        # Cancel all optimization tasks
        for task in self._optimization_tasks:
            if not task.done():
                task.cancel()

        # Wait for tasks to complete
        if self._optimization_tasks:
            await asyncio.gather(*self._optimization_tasks, return_exceptions=True)

        self._optimization_tasks.clear()
        logger.info("Optimization engine shutdown complete")

    def update_performance_data(
        self,
        metrics: dict[MetricType, PerformanceMetric],
        resource_utilization: dict[ResourceType, ResourceUtilization],
        trends: dict[MetricType, Any] | None = None,
    ) -> None:
        """
        Update performance data for optimization analysis.

        Args:
            metrics: Current performance metrics
            resource_utilization: Resource utilization data
            trends: Performance trends (optional)
        """
        self._current_metrics = metrics.copy()
        self._resource_utilization = resource_utilization.copy()
        if trends:
            self._performance_trends = trends.copy()

    def generate_recommendations(self) -> list[OptimizationRecommendation]:
        """
        Generate optimization recommendations based on current performance data.

        Returns:
            List of optimization recommendations
        """
        recommendations = []

        try:
            # Clear existing recommendations
            for category in OptimizationCategory:
                self._recommendations[category] = []

            # Analyze different optimization categories
            recommendations.extend(self._analyze_configuration_optimizations())
            recommendations.extend(self._analyze_resource_optimizations())
            recommendations.extend(self._analyze_protocol_optimizations())
            recommendations.extend(self._analyze_architecture_optimizations())
            recommendations.extend(self._analyze_monitoring_optimizations())

            # Sort by priority and filter by confidence threshold
            high_confidence_recommendations = [
                rec
                for rec in recommendations
                if self._calculate_recommendation_confidence(rec)
                >= self.settings.recommendation_confidence_threshold
            ]

            # Limit recommendations per category
            filtered_recommendations = self._filter_recommendations_by_category(
                high_confidence_recommendations
            )

            # Update statistics
            self._optimization_stats["recommendations_generated"] += len(filtered_recommendations)
            self._optimization_stats["high_priority_recommendations"] += len(
                [rec for rec in filtered_recommendations if rec.priority == "high"]
            )

            for rec in filtered_recommendations:
                self._optimization_stats["recommendations_by_category"][rec.category.value] += 1

            return filtered_recommendations

        except Exception as e:
            logger.error(f"Error generating optimization recommendations: {e}")
            return []

    def get_recommendations_by_category(
        self, category: OptimizationCategory
    ) -> list[OptimizationRecommendation]:
        """Get recommendations for a specific category."""
        return self._recommendations.get(category, [])

    def get_all_recommendations(
        self,
    ) -> dict[OptimizationCategory, list[OptimizationRecommendation]]:
        """Get all current recommendations organized by category."""
        return self._recommendations.copy()

    def get_optimization_statistics(self) -> dict[str, Any]:
        """Get optimization engine statistics."""
        return {
            "enabled": self.settings.enabled and self.settings.enable_optimization_recommendations,
            "running": self._running,
            "total_recommendations": sum(len(recs) for recs in self._recommendations.values()),
            "recommendations_by_category": {
                cat.value: len(recs) for cat, recs in self._recommendations.items()
            },
            "statistics": self._optimization_stats.copy(),
        }

    # Optimization analysis methods

    def _analyze_configuration_optimizations(self) -> list[OptimizationRecommendation]:
        """Analyze configuration-based optimizations."""
        recommendations = []

        # Check telemetry collection interval
        if self.settings.telemetry_collection_interval_seconds > 10.0:
            recommendations.append(
                OptimizationRecommendation(
                    title="Reduce Telemetry Collection Interval",
                    description="Current telemetry collection interval is high. Reducing it will provide more granular performance monitoring.",
                    category=OptimizationCategory.CONFIGURATION,
                    priority="medium",
                    expected_improvement_percent=15.0,
                    affected_metrics=[MetricType.PROCESSING_LATENCY],
                    configuration_changes={"telemetry_collection_interval_seconds": 5.0},
                    implementation_steps=[
                        "Update COACHIQ_PERFORMANCE_ANALYTICS__TELEMETRY_COLLECTION_INTERVAL_SECONDS=5.0",
                        "Restart service to apply changes",
                    ],
                    estimated_effort_hours=0.25,
                    requires_restart=True,
                    risk_level="low",
                )
            )

        # Check memory limit configuration
        current_memory_usage = self._resource_utilization.get(ResourceType.MEMORY)
        if current_memory_usage and current_memory_usage.usage_percent > 70:
            recommendations.append(
                OptimizationRecommendation(
                    title="Increase Memory Limit",
                    description="Memory usage is approaching limits. Increasing memory allocation will improve performance.",
                    category=OptimizationCategory.CONFIGURATION,
                    priority="high",
                    expected_improvement_percent=25.0,
                    affected_metrics=[MetricType.MEMORY_USAGE, MetricType.PROCESSING_LATENCY],
                    affected_resources=[ResourceType.MEMORY],
                    configuration_changes={"memory_limit_mb": self.settings.memory_limit_mb * 1.5},
                    implementation_steps=[
                        f"Update COACHIQ_PERFORMANCE_ANALYTICS__MEMORY_LIMIT_MB={int(self.settings.memory_limit_mb * 1.5)}",
                        "Monitor memory usage after change",
                    ],
                    estimated_effort_hours=0.5,
                    risk_level="low",
                )
            )

        return recommendations

    def _analyze_resource_optimizations(self) -> list[OptimizationRecommendation]:
        """Analyze resource allocation optimizations."""
        recommendations = []

        # CPU optimization
        cpu_usage = self._resource_utilization.get(ResourceType.CPU)
        if (
            cpu_usage
            and cpu_usage.usage_percent > self._optimization_rules["cpu_optimization_threshold"]
        ):
            recommendations.append(
                OptimizationRecommendation(
                    title="Optimize CPU Usage",
                    description=f"CPU usage is {cpu_usage.usage_percent:.1f}%. Consider optimizing processing or scaling resources.",
                    category=OptimizationCategory.RESOURCE,
                    priority="high" if cpu_usage.usage_percent > 85 else "medium",
                    expected_improvement_percent=20.0,
                    affected_resources=[ResourceType.CPU],
                    affected_metrics=[MetricType.CPU_USAGE, MetricType.PROCESSING_LATENCY],
                    implementation_steps=[
                        "Review message processing load",
                        "Consider horizontal scaling",
                        "Optimize CPU-intensive operations",
                        "Enable processing batch optimization",
                    ],
                    configuration_changes={
                        "processing_batch_size": min(self.settings.processing_batch_size * 2, 500),
                        "max_concurrent_analyses": max(
                            self.settings.max_concurrent_analyses - 1, 1
                        ),
                    },
                    estimated_effort_hours=2.0,
                    risk_level="medium",
                )
            )

        # CAN bus load optimization
        can_metrics = [
            m for m in self._current_metrics.values() if m.metric_type == MetricType.CAN_BUS_LOAD
        ]
        high_load_interfaces = [
            m
            for m in can_metrics
            if m.value > self._optimization_rules["can_bus_optimization_threshold"]
        ]

        if high_load_interfaces:
            for metric in high_load_interfaces:
                recommendations.append(
                    OptimizationRecommendation(
                        title=f"Optimize CAN Bus Load on {metric.interface}",
                        description=f"CAN bus load on {metric.interface} is {metric.value:.1f}%. Consider message filtering or load balancing.",
                        category=OptimizationCategory.RESOURCE,
                        priority="high" if metric.value > 80 else "medium",
                        expected_improvement_percent=30.0,
                        affected_metrics=[MetricType.CAN_BUS_LOAD, MetricType.MESSAGE_RATE],
                        implementation_steps=[
                            "Review message priorities",
                            "Implement message filtering",
                            "Consider load balancing across interfaces",
                            "Optimize message batching",
                        ],
                        estimated_effort_hours=4.0,
                        risk_level="medium",
                    )
                )

        return recommendations

    def _analyze_protocol_optimizations(self) -> list[OptimizationRecommendation]:
        """Analyze protocol-specific optimizations."""
        recommendations = []

        # Check protocol throughput
        for protocol in ["rvc", "j1939", "firefly", "spartan_k2"]:
            throughput_metrics = [
                m
                for m in self._current_metrics.values()
                if m.protocol == protocol and "throughput" in m.metric_type.value
            ]

            for metric in throughput_metrics:
                target_rate = getattr(self.settings, f"target_{protocol}_message_rate", 1000.0)
                if (
                    metric.value
                    < target_rate * self._optimization_rules["low_throughput_threshold"]
                ):
                    recommendations.append(
                        OptimizationRecommendation(
                            title=f"Optimize {protocol.upper()} Protocol Performance",
                            description=f"{protocol.upper()} throughput is {metric.value:.0f} msg/s, below target of {target_rate:.0f} msg/s.",
                            category=OptimizationCategory.PROTOCOL,
                            priority="medium",
                            expected_improvement_percent=40.0,
                            affected_metrics=[metric.metric_type],
                            implementation_steps=[
                                f"Review {protocol} message processing pipeline",
                                "Optimize decode/encode operations",
                                "Consider message prioritization",
                                "Enable protocol-specific optimizations",
                            ],
                            configuration_changes={
                                f"protocol_monitoring_enabled.{protocol}": True,
                                f"protocol_priority_weights.{protocol}": 1.2,
                            },
                            estimated_effort_hours=3.0,
                            risk_level="low",
                        )
                    )

        # Check processing latency
        latency_metrics = [
            m
            for m in self._current_metrics.values()
            if m.metric_type == MetricType.PROCESSING_LATENCY
        ]
        high_latency_metrics = [
            m
            for m in latency_metrics
            if m.value > self._optimization_rules["high_latency_threshold"]
        ]

        if high_latency_metrics:
            recommendations.append(
                OptimizationRecommendation(
                    title="Reduce Message Processing Latency",
                    description="Message processing latency is above optimal thresholds. Consider optimization strategies.",
                    category=OptimizationCategory.PROTOCOL,
                    priority="high",
                    expected_improvement_percent=35.0,
                    affected_metrics=[MetricType.PROCESSING_LATENCY, MetricType.DECODE_TIME],
                    implementation_steps=[
                        "Profile message processing pipeline",
                        "Optimize decoding algorithms",
                        "Implement parallel processing",
                        "Cache frequently accessed data",
                    ],
                    estimated_effort_hours=6.0,
                    risk_level="medium",
                )
            )

        return recommendations

    def _analyze_architecture_optimizations(self) -> list[OptimizationRecommendation]:
        """Analyze architecture-level optimizations."""
        recommendations = []

        # Check for high API response times
        api_metrics = [
            m
            for m in self._current_metrics.values()
            if m.metric_type == MetricType.API_RESPONSE_TIME
        ]
        slow_apis = [
            m for m in api_metrics if m.value > self.settings.target_api_response_time_ms * 2
        ]

        if slow_apis:
            recommendations.append(
                OptimizationRecommendation(
                    title="Implement API Response Caching",
                    description="API response times are above optimal. Consider implementing caching and optimization strategies.",
                    category=OptimizationCategory.ARCHITECTURE,
                    priority="medium",
                    expected_improvement_percent=50.0,
                    affected_metrics=[MetricType.API_RESPONSE_TIME],
                    implementation_steps=[
                        "Implement response caching",
                        "Add database query optimization",
                        "Consider API request batching",
                        "Implement async processing where possible",
                    ],
                    estimated_effort_hours=8.0,
                    risk_level="medium",
                )
            )

        # Check WebSocket latency
        ws_metrics = [
            m
            for m in self._current_metrics.values()
            if m.metric_type == MetricType.WEBSOCKET_LATENCY
        ]
        high_latency_ws = [
            m for m in ws_metrics if m.value > self.settings.target_websocket_latency_ms * 3
        ]

        if high_latency_ws:
            recommendations.append(
                OptimizationRecommendation(
                    title="Optimize WebSocket Performance",
                    description="WebSocket latency is high. Consider connection pooling and message optimization.",
                    category=OptimizationCategory.ARCHITECTURE,
                    priority="medium",
                    expected_improvement_percent=45.0,
                    affected_metrics=[MetricType.WEBSOCKET_LATENCY],
                    implementation_steps=[
                        "Implement WebSocket connection pooling",
                        "Optimize message serialization",
                        "Consider message compression",
                        "Implement client-side buffering",
                    ],
                    estimated_effort_hours=6.0,
                    risk_level="medium",
                )
            )

        return recommendations

    def _analyze_monitoring_optimizations(self) -> list[OptimizationRecommendation]:
        """Analyze monitoring and observability optimizations."""
        recommendations = []

        # Check if debug metrics are enabled with high sample rate
        if self.settings.enable_debug_metrics and self.settings.debug_metric_sample_rate > 0.5:
            recommendations.append(
                OptimizationRecommendation(
                    title="Optimize Debug Metrics Sampling",
                    description="Debug metrics sampling rate is high, which may impact performance. Consider reducing the sample rate.",
                    category=OptimizationCategory.MONITORING,
                    priority="low",
                    expected_improvement_percent=10.0,
                    affected_metrics=[MetricType.CPU_USAGE, MetricType.MEMORY_USAGE],
                    configuration_changes={"debug_metric_sample_rate": 0.1},
                    implementation_steps=[
                        "Update COACHIQ_PERFORMANCE_ANALYTICS__DEBUG_METRIC_SAMPLE_RATE=0.1",
                        "Monitor impact on performance metrics",
                    ],
                    estimated_effort_hours=0.25,
                    risk_level="low",
                )
            )

        # Check metric retention
        if self.settings.metric_retention_hours > 48:
            recommendations.append(
                OptimizationRecommendation(
                    title="Optimize Metric Retention Period",
                    description="Long metric retention period may impact memory usage. Consider reducing retention time.",
                    category=OptimizationCategory.MONITORING,
                    priority="low",
                    expected_improvement_percent=5.0,
                    affected_metrics=[MetricType.MEMORY_USAGE],
                    configuration_changes={"metric_retention_hours": 24},
                    implementation_steps=[
                        "Update COACHIQ_PERFORMANCE_ANALYTICS__METRIC_RETENTION_HOURS=24",
                        "Implement metric archiving if long-term data is needed",
                    ],
                    estimated_effort_hours=1.0,
                    risk_level="low",
                )
            )

        return recommendations

    def _calculate_recommendation_confidence(
        self, recommendation: OptimizationRecommendation
    ) -> float:
        """Calculate confidence score for a recommendation."""
        base_confidence = 0.7

        # Increase confidence based on affected metrics and evidence
        if recommendation.affected_metrics:
            base_confidence += 0.1

        if (
            recommendation.expected_improvement_percent
            and recommendation.expected_improvement_percent > 20
        ):
            base_confidence += 0.1

        # Adjust based on risk level
        if recommendation.risk_level == "low":
            base_confidence += 0.1
        elif recommendation.risk_level == "high":
            base_confidence -= 0.2

        return min(1.0, base_confidence)

    def _filter_recommendations_by_category(
        self, recommendations: list[OptimizationRecommendation]
    ) -> list[OptimizationRecommendation]:
        """Filter recommendations to respect category limits."""
        filtered = []
        category_counts = dict.fromkeys(OptimizationCategory, 0)

        # Sort by priority (high first) and expected improvement
        sorted_recs = sorted(
            recommendations,
            key=lambda r: (
                r.priority == "high",
                r.expected_improvement_percent or 0,
                r.priority == "medium",
            ),
            reverse=True,
        )

        for rec in sorted_recs:
            if category_counts[rec.category] < self.settings.max_recommendations_per_category:
                filtered.append(rec)
                category_counts[rec.category] += 1
                self._recommendations[rec.category].append(rec)

        return filtered

    # Background optimization tasks

    async def _optimization_analysis_loop(self) -> None:
        """Background task for optimization analysis."""
        while self._running:
            try:
                # Generate recommendations based on current data
                if self._current_metrics or self._resource_utilization:
                    recommendations = self.generate_recommendations()
                    logger.debug(f"Generated {len(recommendations)} optimization recommendations")

                self._optimization_stats["optimization_cycles"] += 1

                # Sleep for optimization analysis interval
                await asyncio.sleep(3600.0)  # Analyze every hour

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in optimization analysis: {e}")
                await asyncio.sleep(600.0)  # Wait 10 minutes on error
