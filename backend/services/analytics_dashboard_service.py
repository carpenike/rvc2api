"""
Advanced Analytics Dashboard Service

Provides comprehensive analytics dashboard functionality including performance trends,
system insights, historical data analysis, and intelligent recommendations.

This service aggregates data from various sources to provide business intelligence
and operational insights for the RV-C system.
"""

import asyncio
import contextlib
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from backend.core.config import get_settings
from backend.services.feature_manager import get_feature_manager

logger = logging.getLogger(__name__)


@dataclass
class TrendPoint:
    """Data point for trend analysis."""

    timestamp: float
    value: float
    baseline_deviation: float = 0.0
    anomaly_score: float = 0.0


@dataclass
class SystemInsight:
    """System insight with actionable recommendations."""

    insight_id: str
    category: str  # performance, reliability, efficiency, cost
    title: str
    description: str
    severity: str  # low, medium, high, critical
    confidence: float  # 0.0-1.0
    impact_score: float  # 0.0-1.0
    recommendations: list[str]
    supporting_data: dict[str, Any]
    created_at: float


@dataclass
class PatternAnalysis:
    """Pattern detection results."""

    pattern_id: str
    pattern_type: str  # cyclical, trending, anomalous, baseline
    description: str
    confidence: float
    frequency: str | None = None  # hourly, daily, weekly
    correlation_factors: list[str] = field(default_factory=list)
    prediction_window: int | None = None  # hours into future


@dataclass
class MetricsAggregation:
    """Aggregated metrics for reporting."""

    metric_name: str
    time_window: str
    aggregation_type: str  # avg, min, max, sum, count
    current_value: float
    previous_value: float
    change_percent: float
    trend_direction: str  # up, down, stable
    distribution: dict[str, float]  # percentiles, quartiles


class AnalyticsDashboardService:
    """
    Advanced analytics dashboard service providing comprehensive insights.

    This service provides:
    - Performance trend analysis and visualization
    - System health insights and recommendations
    - Historical pattern detection and analysis
    - Comprehensive metrics aggregation and reporting
    """

    def __init__(self):
        """Initialize the analytics dashboard service."""
        self.config = get_settings()
        self.feature_manager = get_feature_manager()

        # Data storage for analytics
        self.metric_history: dict[str, list[TrendPoint]] = defaultdict(list)
        self.insights_cache: list[SystemInsight] = []
        self.pattern_cache: list[PatternAnalysis] = []

        # Configuration
        self.history_retention_hours = 24 * 7  # 7 days default
        self.insight_generation_interval = 300  # 5 minutes
        self.pattern_analysis_interval = 1800  # 30 minutes

        # Background tasks
        self._insight_task: asyncio.Task | None = None
        self._pattern_task: asyncio.Task | None = None
        self._running = False

        logger.info("AnalyticsDashboardService initialized")

    async def start(self) -> None:
        """Start the analytics dashboard service."""
        if self._running:
            logger.warning("Analytics dashboard service already running")
            return

        self._running = True

        # Start background analysis tasks
        self._insight_task = asyncio.create_task(self._insight_generation_loop())
        self._pattern_task = asyncio.create_task(self._pattern_analysis_loop())

        logger.info("Analytics dashboard service started")

    async def stop(self) -> None:
        """Stop the analytics dashboard service."""
        self._running = False

        if self._insight_task:
            self._insight_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._insight_task

        if self._pattern_task:
            self._pattern_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._pattern_task

        logger.info("Analytics dashboard service stopped")

    async def get_performance_trends(
        self,
        time_window_hours: int = 24,
        metrics: list[str] | None = None,
        resolution: str = "1h",
    ) -> dict[str, Any]:
        """
        Get performance trends for specified metrics and time window.

        Args:
            time_window_hours: Time window for trend analysis
            metrics: Specific metrics to include (None for all)
            resolution: Data resolution (1m, 5m, 15m, 1h, 6h, 1d)

        Returns:
            Performance trend data with analysis
        """
        logger.debug(f"Generating performance trends for {time_window_hours}h window")

        cutoff_time = time.time() - (time_window_hours * 3600)

        # Get performance analytics feature
        perf_feature = self.feature_manager.get_feature("performance_analytics")
        if not perf_feature:
            return self._empty_trends_response()

        trends = {
            "time_window_hours": time_window_hours,
            "resolution": resolution,
            "metrics": {},
            "summary": {},
            "alerts": [],
            "insights": [],
        }

        try:
            # Generate trend data for each metric
            target_metrics = metrics or [
                "protocol_throughput",
                "api_response_time",
                "websocket_latency",
                "can_message_rate",
                "error_rate",
                "system_load",
            ]

            for metric_name in target_metrics:
                trend_data = await self._calculate_metric_trend(
                    metric_name, cutoff_time, resolution
                )
                trends["metrics"][metric_name] = trend_data

            # Generate summary insights
            trends["summary"] = await self._generate_trend_summary(trends["metrics"])

            # Check for performance alerts
            trends["alerts"] = await self._detect_performance_alerts(trends["metrics"])

            # Include recent insights
            trends["insights"] = [
                insight
                for insight in self.insights_cache
                if insight.category == "performance" and insight.created_at > cutoff_time
            ]

            logger.info(f"Generated trends for {len(target_metrics)} metrics")
            return trends

        except Exception as e:
            logger.error(f"Error generating performance trends: {e}", exc_info=True)
            return self._empty_trends_response()

    async def get_system_insights(
        self,
        categories: list[str] | None = None,
        min_severity: str = "low",
        limit: int = 50,
    ) -> dict[str, Any]:
        """
        Get system insights and recommendations.

        Args:
            categories: Insight categories to include
            min_severity: Minimum severity level
            limit: Maximum number of insights

        Returns:
            System insights with recommendations
        """
        logger.debug(f"Retrieving system insights with min_severity={min_severity}")

        # Filter insights by criteria
        filtered_insights = []
        severity_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        min_severity_level = severity_order.get(min_severity, 0)

        for insight in self.insights_cache:
            # Check severity
            if severity_order.get(insight.severity, 0) < min_severity_level:
                continue

            # Check categories
            if categories and insight.category not in categories:
                continue

            filtered_insights.append(insight)

        # Sort by severity and impact
        filtered_insights.sort(
            key=lambda x: (
                -severity_order.get(x.severity, 0),
                -x.impact_score,
                -x.confidence,
            )
        )

        # Limit results
        filtered_insights = filtered_insights[:limit]

        # Generate insights summary
        insights_summary = await self._generate_insights_summary(filtered_insights)

        return {
            "total_insights": len(filtered_insights),
            "insights": [self._serialize_insight(insight) for insight in filtered_insights],
            "summary": insights_summary,
            "categories": list({insight.category for insight in filtered_insights}),
            "severity_distribution": self._calculate_severity_distribution(filtered_insights),
        }

    async def get_historical_analysis(
        self,
        analysis_type: str = "pattern_detection",
        time_window_hours: int = 168,  # 7 days
        include_predictions: bool = True,
    ) -> dict[str, Any]:
        """
        Get historical data analysis including pattern detection.

        Args:
            analysis_type: Type of analysis (pattern_detection, anomaly_detection, correlation)
            time_window_hours: Time window for analysis
            include_predictions: Whether to include predictive analysis

        Returns:
            Historical analysis results
        """
        logger.debug(f"Performing historical analysis: {analysis_type}")

        cutoff_time = time.time() - (time_window_hours * 3600)

        analysis = {
            "analysis_type": analysis_type,
            "time_window_hours": time_window_hours,
            "patterns": [],
            "anomalies": [],
            "correlations": [],
            "predictions": [],
            "summary": {},
        }

        try:
            if analysis_type in ["pattern_detection", "all"]:
                patterns = [pattern for pattern in self.pattern_cache if pattern.confidence > 0.5]
                analysis["patterns"] = [self._serialize_pattern(p) for p in patterns]

            if analysis_type in ["anomaly_detection", "all"]:
                anomalies = await self._detect_historical_anomalies(cutoff_time)
                analysis["anomalies"] = anomalies

            if analysis_type in ["correlation", "all"]:
                correlations = await self._analyze_metric_correlations(cutoff_time)
                analysis["correlations"] = correlations

            if include_predictions:
                predictions = await self._generate_predictions(cutoff_time)
                analysis["predictions"] = predictions

            # Generate analysis summary
            analysis["summary"] = await self._generate_analysis_summary(analysis)

            logger.info(f"Historical analysis completed: {analysis_type}")
            return analysis

        except Exception as e:
            logger.error(f"Error in historical analysis: {e}", exc_info=True)
            return analysis

    async def get_metrics_aggregation(
        self,
        aggregation_windows: list[str] | None = None,
        metric_groups: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Get comprehensive metrics aggregation and reporting.

        Args:
            aggregation_windows: Time windows for aggregation (1h, 6h, 1d, 1w)
            metric_groups: Metric groups to include

        Returns:
            Aggregated metrics with reporting data
        """
        aggregation_windows = aggregation_windows or ["1h", "6h", "1d", "1w"]
        metric_groups = metric_groups or [
            "system_performance",
            "protocol_efficiency",
            "user_activity",
            "error_rates",
        ]

        logger.debug(f"Generating metrics aggregation for {len(aggregation_windows)} windows")

        aggregation = {
            "windows": {},
            "kpis": {},
            "trends": {},
            "benchmarks": {},
            "recommendations": [],
        }

        try:
            for window in aggregation_windows:
                window_data = await self._aggregate_metrics_for_window(window, metric_groups)
                aggregation["windows"][window] = window_data

            # Calculate KPIs
            aggregation["kpis"] = await self._calculate_key_performance_indicators()

            # Generate trend analysis
            aggregation["trends"] = await self._analyze_aggregation_trends(aggregation["windows"])

            # Get performance benchmarks
            aggregation["benchmarks"] = await self._get_performance_benchmarks()

            # Generate optimization recommendations
            aggregation["recommendations"] = await self._generate_optimization_recommendations(
                aggregation
            )

            logger.info("Metrics aggregation completed successfully")
            return aggregation

        except Exception as e:
            logger.error(f"Error in metrics aggregation: {e}", exc_info=True)
            return aggregation

    async def record_custom_metric(
        self, metric_name: str, value: float, metadata: dict[str, Any] | None = None
    ) -> bool:
        """
        Record a custom metric for analytics.

        Args:
            metric_name: Name of the metric
            value: Metric value
            metadata: Additional metadata

        Returns:
            Success status
        """
        try:
            timestamp = time.time()

            # Calculate baseline deviation if we have history
            baseline_deviation = 0.0
            if metric_name in self.metric_history:
                recent_values = [point.value for point in self.metric_history[metric_name][-10:]]
                if recent_values:
                    baseline = sum(recent_values) / len(recent_values)
                    baseline_deviation = (
                        ((value - baseline) / baseline) * 100 if baseline > 0 else 0
                    )

            # Create trend point
            trend_point = TrendPoint(
                timestamp=timestamp, value=value, baseline_deviation=baseline_deviation
            )

            # Add to history
            self.metric_history[metric_name].append(trend_point)

            # Cleanup old data
            cutoff_time = timestamp - (self.history_retention_hours * 3600)
            self.metric_history[metric_name] = [
                point for point in self.metric_history[metric_name] if point.timestamp > cutoff_time
            ]

            logger.debug(f"Recorded custom metric: {metric_name}={value}")
            return True

        except Exception as e:
            logger.error(f"Error recording custom metric: {e}", exc_info=True)
            return False

    # Helper methods for analytics processing

    async def _get_current_performance_metrics(self) -> dict[str, float]:
        """Get current performance metrics from various sources."""
        metrics = {}

        try:
            # Get metrics from performance analytics feature
            perf_feature = self.feature_manager.get_feature("performance_analytics")
            if perf_feature and hasattr(perf_feature, "get_current_metrics"):
                current_metrics = await perf_feature.get_current_metrics()
                metrics.update(current_metrics)

            # Add system-level metrics
            metrics.update(
                {
                    "timestamp": time.time(),
                    "active_features": len(
                        [f for f in self.feature_manager.features.values() if f.enabled]
                    ),
                    "memory_usage": 0.0,  # Would be populated from system monitoring
                    "cpu_usage": 0.0,
                }
            )

        except Exception as e:
            logger.error(f"Error getting current metrics: {e}")

        return metrics

    async def _calculate_metric_trend(
        self, metric_name: str, cutoff_time: float, resolution: str
    ) -> dict[str, Any]:
        """Calculate trend data for a specific metric."""
        if metric_name not in self.metric_history:
            return {
                "data_points": [],
                "trend_direction": "stable",
                "change_percent": 0.0,
                "anomaly_count": 0,
            }

        # Filter data points by time
        points = [
            point for point in self.metric_history[metric_name] if point.timestamp > cutoff_time
        ]

        if len(points) < 2:
            return {
                "data_points": [],
                "trend_direction": "stable",
                "change_percent": 0.0,
                "anomaly_count": 0,
            }

        # Calculate trend direction
        first_value = points[0].value
        last_value = points[-1].value
        change_percent = ((last_value - first_value) / first_value) * 100 if first_value > 0 else 0

        if abs(change_percent) < 5:
            trend_direction = "stable"
        elif change_percent > 0:
            trend_direction = "up"
        else:
            trend_direction = "down"

        # Count anomalies (points with high baseline deviation)
        anomaly_count = sum(1 for point in points if abs(point.baseline_deviation) > 20)

        return {
            "data_points": [
                {
                    "timestamp": point.timestamp,
                    "value": point.value,
                    "baseline_deviation": point.baseline_deviation,
                }
                for point in points
            ],
            "trend_direction": trend_direction,
            "change_percent": round(change_percent, 2),
            "anomaly_count": anomaly_count,
            "data_quality": "good" if len(points) > 10 else "limited",
        }

    async def _generate_trend_summary(self, metrics: dict[str, Any]) -> dict[str, Any]:
        """Generate summary of trend analysis."""
        summary = {
            "total_metrics": len(metrics),
            "trending_up": 0,
            "trending_down": 0,
            "stable": 0,
            "total_anomalies": 0,
            "key_insights": [],
        }

        for _metric_name, trend_data in metrics.items():
            direction = trend_data.get("trend_direction", "stable")
            if direction == "up":
                summary["trending_up"] += 1
            elif direction == "down":
                summary["trending_down"] += 1
            else:
                summary["stable"] += 1

            summary["total_anomalies"] += trend_data.get("anomaly_count", 0)

        # Generate key insights
        if summary["trending_down"] > summary["trending_up"]:
            summary["key_insights"].append("System performance showing declining trends")
        elif summary["trending_up"] > summary["trending_down"]:
            summary["key_insights"].append("System performance showing improvement")
        else:
            summary["key_insights"].append("System performance is stable")

        if summary["total_anomalies"] > 5:
            summary["key_insights"].append("Multiple performance anomalies detected")

        return summary

    async def _detect_performance_alerts(self, metrics: dict[str, Any]) -> list[dict[str, Any]]:
        """Detect performance alerts from trend data."""
        alerts = []

        for metric_name, trend_data in metrics.items():
            # High anomaly count alert
            anomaly_count = trend_data.get("anomaly_count", 0)
            if anomaly_count > 3:
                alerts.append(
                    {
                        "type": "performance_anomaly",
                        "severity": "medium" if anomaly_count < 10 else "high",
                        "metric": metric_name,
                        "message": f"High anomaly count detected: {anomaly_count} anomalies",
                        "recommendation": f"Investigate {metric_name} performance patterns",
                    }
                )

            # Significant degradation alert
            change_percent = trend_data.get("change_percent", 0)
            if change_percent < -20:
                alerts.append(
                    {
                        "type": "performance_degradation",
                        "severity": "high",
                        "metric": metric_name,
                        "message": f"Significant performance degradation: {change_percent:.1f}%",
                        "recommendation": f"Urgent attention needed for {metric_name}",
                    }
                )

        return alerts

    async def _insight_generation_loop(self) -> None:
        """Background task for generating system insights."""
        while self._running:
            try:
                await self._generate_system_insights()
                await asyncio.sleep(self.insight_generation_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in insight generation loop: {e}")
                await asyncio.sleep(60)  # Wait before retrying

    async def _pattern_analysis_loop(self) -> None:
        """Background task for pattern analysis."""
        while self._running:
            try:
                await self._analyze_patterns()
                await asyncio.sleep(self.pattern_analysis_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in pattern analysis loop: {e}")
                await asyncio.sleep(120)  # Wait before retrying

    async def _generate_system_insights(self) -> None:
        """Generate system insights and recommendations."""
        try:
            current_time = time.time()

            # Performance insights
            performance_insights = await self._analyze_performance_insights()

            # Reliability insights
            reliability_insights = await self._analyze_reliability_insights()

            # Efficiency insights
            efficiency_insights = await self._analyze_efficiency_insights()

            # Add new insights to cache
            new_insights = performance_insights + reliability_insights + efficiency_insights
            self.insights_cache.extend(new_insights)

            # Cleanup old insights (keep only last 24 hours)
            cutoff_time = current_time - (24 * 3600)
            self.insights_cache = [
                insight for insight in self.insights_cache if insight.created_at > cutoff_time
            ]

            logger.debug(f"Generated {len(new_insights)} new insights")

        except Exception as e:
            logger.error(f"Error generating system insights: {e}")

    async def _analyze_patterns(self) -> None:
        """Analyze historical data for patterns."""
        try:
            # Analyze each metric for patterns
            new_patterns = []

            for metric_name, history in self.metric_history.items():
                if len(history) < 20:  # Need sufficient data
                    continue

                # Simple pattern detection (would be enhanced with ML)
                patterns = await self._detect_metric_patterns(metric_name, history)
                new_patterns.extend(patterns)

            # Update pattern cache
            self.pattern_cache = new_patterns

            logger.debug(f"Analyzed patterns for {len(self.metric_history)} metrics")

        except Exception as e:
            logger.error(f"Error analyzing patterns: {e}")

    def _empty_trends_response(self) -> dict[str, Any]:
        """Return empty trends response structure."""
        return {
            "time_window_hours": 24,
            "resolution": "1h",
            "metrics": {},
            "summary": {
                "total_metrics": 0,
                "trending_up": 0,
                "trending_down": 0,
                "stable": 0,
                "total_anomalies": 0,
                "key_insights": ["No performance data available"],
            },
            "alerts": [],
            "insights": [],
        }

    def _serialize_insight(self, insight: SystemInsight) -> dict[str, Any]:
        """Serialize system insight for API response."""
        return {
            "insight_id": insight.insight_id,
            "category": insight.category,
            "title": insight.title,
            "description": insight.description,
            "severity": insight.severity,
            "confidence": round(insight.confidence, 2),
            "impact_score": round(insight.impact_score, 2),
            "recommendations": insight.recommendations,
            "supporting_data": insight.supporting_data,
            "created_at": insight.created_at,
        }

    def _serialize_pattern(self, pattern: PatternAnalysis) -> dict[str, Any]:
        """Serialize pattern analysis for API response."""
        return {
            "pattern_id": pattern.pattern_id,
            "pattern_type": pattern.pattern_type,
            "description": pattern.description,
            "confidence": round(pattern.confidence, 2),
            "frequency": pattern.frequency,
            "correlation_factors": pattern.correlation_factors,
            "prediction_window": pattern.prediction_window,
        }

    # Placeholder methods for advanced analytics (would be enhanced with ML/AI)

    async def _analyze_performance_insights(self) -> list[SystemInsight]:
        """Analyze performance data for insights."""
        return []  # Would implement ML-based performance analysis

    async def _analyze_reliability_insights(self) -> list[SystemInsight]:
        """Analyze system reliability for insights."""
        return []  # Would implement reliability pattern analysis

    async def _analyze_efficiency_insights(self) -> list[SystemInsight]:
        """Analyze system efficiency for insights."""
        return []  # Would implement efficiency optimization analysis

    async def _detect_metric_patterns(
        self, metric_name: str, history: list[TrendPoint]
    ) -> list[PatternAnalysis]:
        """Detect patterns in metric history."""
        return []  # Would implement pattern detection algorithms

    async def _detect_historical_anomalies(self, cutoff_time: float) -> list[dict[str, Any]]:
        """Detect anomalies in historical data."""
        return []  # Would implement anomaly detection

    async def _analyze_metric_correlations(self, cutoff_time: float) -> list[dict[str, Any]]:
        """Analyze correlations between metrics."""
        return []  # Would implement correlation analysis

    async def _generate_predictions(self, cutoff_time: float) -> list[dict[str, Any]]:
        """Generate predictions based on historical data."""
        return []  # Would implement predictive analytics

    async def _generate_analysis_summary(self, analysis: dict[str, Any]) -> dict[str, Any]:
        """Generate summary of historical analysis."""
        return {
            "patterns_found": len(analysis.get("patterns", [])),
            "anomalies_detected": len(analysis.get("anomalies", [])),
            "correlations_found": len(analysis.get("correlations", [])),
            "predictions_generated": len(analysis.get("predictions", [])),
            "data_quality": "good",
            "confidence": 0.8,
        }

    async def _aggregate_metrics_for_window(
        self, window: str, metric_groups: list[str]
    ) -> dict[str, Any]:
        """Aggregate metrics for a specific time window."""
        return {}  # Would implement metrics aggregation logic

    async def _calculate_key_performance_indicators(self) -> dict[str, float]:
        """Calculate KPIs from aggregated data."""
        return {}  # Would implement KPI calculations

    async def _analyze_aggregation_trends(self, windows: dict[str, Any]) -> dict[str, Any]:
        """Analyze trends across aggregation windows."""
        return {}  # Would implement trend analysis

    async def _get_performance_benchmarks(self) -> dict[str, Any]:
        """Get performance benchmarks for comparison."""
        return {}  # Would implement benchmark data

    async def _generate_optimization_recommendations(
        self, aggregation: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Generate optimization recommendations."""
        return []  # Would implement recommendation engine

    async def _generate_insights_summary(self, insights: list[SystemInsight]) -> dict[str, Any]:
        """Generate summary of insights."""
        if not insights:
            return {
                "total_count": 0,
                "avg_confidence": 0.0,
                "avg_impact": 0.0,
                "top_categories": [],
                "action_required": False,
            }

        return {
            "total_count": len(insights),
            "avg_confidence": sum(i.confidence for i in insights) / len(insights),
            "avg_impact": sum(i.impact_score for i in insights) / len(insights),
            "top_categories": list({i.category for i in insights[:5]}),
            "action_required": any(i.severity in ["high", "critical"] for i in insights),
        }

    def _calculate_severity_distribution(self, insights: list[SystemInsight]) -> dict[str, int]:
        """Calculate distribution of insight severities."""
        distribution = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        for insight in insights:
            distribution[insight.severity] = distribution.get(insight.severity, 0) + 1
        return distribution
