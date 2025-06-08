"""
Performance Benchmarking Engine

Establishes performance baselines and detects deviations from normal operating parameters.
Provides statistical analysis of performance trends and threshold management.
"""

import asyncio
import logging
import statistics
import time
from collections import defaultdict, deque
from typing import Any

from backend.integrations.analytics.config import PerformanceAnalyticsSettings
from backend.integrations.analytics.models import MetricType, PerformanceBaseline, PerformanceMetric

logger = logging.getLogger(__name__)


class BenchmarkingEngine:
    """
    Performance benchmarking engine for baseline establishment and deviation detection.

    Provides capabilities for:
    - Establishing performance baselines from historical data
    - Detecting deviations from established baselines
    - Statistical analysis of performance trends
    - Adaptive threshold management
    """

    def __init__(self, settings: PerformanceAnalyticsSettings):
        """Initialize the benchmarking engine."""
        self.settings = settings

        # Baseline storage
        self._baselines: dict[MetricType, PerformanceBaseline] = {}
        self._baseline_data: dict[MetricType, deque] = defaultdict(lambda: deque(maxlen=10000))

        # Deviation tracking
        self._deviation_alerts: dict[MetricType, list[dict[str, Any]]] = defaultdict(list)
        self._last_baseline_update: dict[MetricType, float] = {}

        # Statistical analysis
        self._trend_data: dict[MetricType, list[tuple[float, float]]] = defaultdict(list)

        # Background tasks
        self._analysis_tasks: list[asyncio.Task] = []
        self._running = False

        # Engine statistics
        self._benchmark_stats = {
            "baselines_established": 0,
            "deviations_detected": 0,
            "baseline_updates": 0,
            "analysis_cycles": 0,
        }

        logger.info("Benchmarking engine initialized")

    async def startup(self) -> None:
        """Start benchmarking engine tasks."""
        if not self.settings.enabled or not self.settings.enable_benchmarking:
            logger.info("Benchmarking engine disabled")
            return

        self._running = True

        # Start baseline analysis task
        analysis_task = asyncio.create_task(self._baseline_analysis_loop())
        self._analysis_tasks.append(analysis_task)

        # Start deviation monitoring task
        monitoring_task = asyncio.create_task(self._deviation_monitoring_loop())
        self._analysis_tasks.append(monitoring_task)

        logger.info("Benchmarking engine started")

    async def shutdown(self) -> None:
        """Shutdown benchmarking engine."""
        self._running = False

        # Cancel all analysis tasks
        for task in self._analysis_tasks:
            if not task.done():
                task.cancel()

        # Wait for tasks to complete
        if self._analysis_tasks:
            await asyncio.gather(*self._analysis_tasks, return_exceptions=True)

        self._analysis_tasks.clear()
        logger.info("Benchmarking engine shutdown complete")

    def record_metric_for_baseline(self, metric: PerformanceMetric) -> None:
        """
        Record a metric for baseline establishment.

        Args:
            metric: Performance metric to record
        """
        if not self.settings.enable_benchmarking:
            return

        self._baseline_data[metric.metric_type].append(metric)

        # Check if we have enough data to establish or update baseline
        current_time = time.time()
        data_points = self._baseline_data[metric.metric_type]

        if len(data_points) >= self._get_minimum_samples_for_baseline():
            last_update = self._last_baseline_update.get(metric.metric_type, 0)
            update_interval = self.settings.baseline_update_interval_hours * 3600

            if current_time - last_update >= update_interval:
                self._update_baseline(metric.metric_type)

    def check_deviation(self, metric: PerformanceMetric) -> tuple[bool, float, str]:
        """
        Check if a metric deviates from its baseline.

        Args:
            metric: Performance metric to check

        Returns:
            Tuple of (is_deviated, deviation_percent, severity)
        """
        baseline = self._baselines.get(metric.metric_type)
        if not baseline:
            return False, 0.0, "no_baseline"

        is_deviated, deviation_percent = baseline.check_deviation(metric.value)

        # Determine severity
        if deviation_percent >= baseline.critical_deviation_percent:
            severity = "critical"
        elif deviation_percent >= baseline.warning_deviation_percent:
            severity = "warning"
        else:
            severity = "normal"

        if is_deviated:
            self._record_deviation_alert(metric, baseline, deviation_percent, severity)

        return is_deviated, deviation_percent, severity

    def get_baseline(self, metric_type: MetricType) -> PerformanceBaseline | None:
        """Get baseline for a specific metric type."""
        return self._baselines.get(metric_type)

    def get_all_baselines(self) -> dict[MetricType, PerformanceBaseline]:
        """Get all established baselines."""
        return self._baselines.copy()

    def get_deviation_alerts(
        self, metric_type: MetricType | None = None, time_window_seconds: float = 3600.0
    ) -> list[dict[str, Any]]:
        """
        Get recent deviation alerts.

        Args:
            metric_type: Specific metric type or None for all
            time_window_seconds: Time window for alerts

        Returns:
            List of deviation alerts
        """
        current_time = time.time()
        cutoff_time = current_time - time_window_seconds

        if metric_type:
            alerts = self._deviation_alerts.get(metric_type, [])
            return [alert for alert in alerts if alert["timestamp"] >= cutoff_time]

        all_alerts = []
        for alerts_list in self._deviation_alerts.values():
            all_alerts.extend([alert for alert in alerts_list if alert["timestamp"] >= cutoff_time])

        return sorted(all_alerts, key=lambda a: a["timestamp"], reverse=True)

    def get_benchmark_statistics(self) -> dict[str, Any]:
        """Get benchmarking engine statistics."""
        return {
            "enabled": self.settings.enabled and self.settings.enable_benchmarking,
            "running": self._running,
            "baselines_count": len(self._baselines),
            "baseline_metrics": [mt.value for mt in self._baselines],
            "data_points": {mt.value: len(data) for mt, data in self._baseline_data.items()},
            "statistics": self._benchmark_stats.copy(),
            "deviation_alerts_count": {
                mt.value: len(alerts) for mt, alerts in self._deviation_alerts.items()
            },
        }

    def force_baseline_update(self, metric_type: MetricType) -> bool:
        """
        Force an immediate baseline update for a metric type.

        Args:
            metric_type: Metric type to update

        Returns:
            True if baseline was updated
        """
        if metric_type not in self._baseline_data:
            return False

        data_points = self._baseline_data[metric_type]
        if len(data_points) < self._get_minimum_samples_for_baseline():
            return False

        return self._update_baseline(metric_type)

    # Internal methods

    def _get_minimum_samples_for_baseline(self) -> int:
        """Get minimum number of samples needed for baseline establishment."""
        # Calculate based on establishment hours and collection interval
        samples_per_hour = 3600 / self.settings.telemetry_collection_interval_seconds
        return max(int(samples_per_hour * self.settings.baseline_establishment_hours), 10)

    def _update_baseline(self, metric_type: MetricType) -> bool:
        """
        Update baseline for a specific metric type.

        Args:
            metric_type: Metric type to update

        Returns:
            True if baseline was updated successfully
        """
        try:
            data_points = self._baseline_data[metric_type]
            if not data_points:
                return False

            # Extract values for statistical analysis
            values = [point.value for point in data_points]

            # Calculate statistical properties
            mean_value = statistics.mean(values)
            std_dev = statistics.stdev(values) if len(values) > 1 else 0.0
            min_value = min(values)
            max_value = max(values)

            # Calculate percentiles
            sorted_values = sorted(values)
            percentile_95_index = int(0.95 * len(sorted_values))
            percentile_95 = sorted_values[percentile_95_index] if sorted_values else mean_value

            # Create or update baseline
            current_time = time.time()
            if metric_type in self._baselines:
                baseline = self._baselines[metric_type]
                baseline.baseline_value = mean_value
                baseline.mean = mean_value
                baseline.std_dev = std_dev
                baseline.min_value = min_value
                baseline.max_value = max_value
                baseline.percentile_95 = percentile_95
                baseline.sample_count = len(values)
                baseline.established_at = current_time

                # Update deviation thresholds from settings
                baseline.warning_deviation_percent = (
                    self.settings.deviation_warning_threshold_percent
                )
                baseline.critical_deviation_percent = (
                    self.settings.deviation_critical_threshold_percent
                )

                self._benchmark_stats["baseline_updates"] += 1
            else:
                baseline = PerformanceBaseline(
                    metric_type=metric_type,
                    baseline_value=mean_value,
                    established_at=current_time,
                    mean=mean_value,
                    std_dev=std_dev,
                    min_value=min_value,
                    max_value=max_value,
                    percentile_95=percentile_95,
                    sample_count=len(values),
                    warning_deviation_percent=self.settings.deviation_warning_threshold_percent,
                    critical_deviation_percent=self.settings.deviation_critical_threshold_percent,
                )
                self._baselines[metric_type] = baseline
                self._benchmark_stats["baselines_established"] += 1

            self._last_baseline_update[metric_type] = current_time

            logger.info(
                f"Updated baseline for {metric_type.value}: {mean_value:.2f} "
                f"(std: {std_dev:.2f}, samples: {len(values)})"
            )

            return True

        except Exception as e:
            logger.error(f"Error updating baseline for {metric_type.value}: {e}")
            return False

    def _record_deviation_alert(
        self,
        metric: PerformanceMetric,
        baseline: PerformanceBaseline,
        deviation_percent: float,
        severity: str,
    ) -> None:
        """Record a deviation alert."""
        alert = {
            "timestamp": time.time(),
            "metric_type": metric.metric_type.value,
            "current_value": metric.value,
            "baseline_value": baseline.baseline_value,
            "deviation_percent": deviation_percent,
            "severity": severity,
            "protocol": metric.protocol,
            "interface": metric.interface,
            "component": metric.component,
            "unit": metric.unit,
        }

        self._deviation_alerts[metric.metric_type].append(alert)

        # Limit alert history
        if len(self._deviation_alerts[metric.metric_type]) > 1000:
            self._deviation_alerts[metric.metric_type] = self._deviation_alerts[metric.metric_type][
                -500:
            ]

        self._benchmark_stats["deviations_detected"] += 1

        logger.warning(
            f"Performance deviation detected: {metric.metric_type.value} "
            f"{metric.value:.2f} vs baseline {baseline.baseline_value:.2f} "
            f"({deviation_percent:.1f}% deviation, {severity})"
        )

    # Background analysis tasks

    async def _baseline_analysis_loop(self) -> None:
        """Background task for baseline analysis and updates."""
        while self._running:
            try:
                await self._perform_baseline_analysis()

                # Sleep for baseline update interval
                sleep_time = (
                    self.settings.baseline_update_interval_hours * 3600 / 4
                )  # Check 4x per update interval
                await asyncio.sleep(sleep_time)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in baseline analysis: {e}")
                await asyncio.sleep(300.0)  # Wait 5 minutes on error

    async def _deviation_monitoring_loop(self) -> None:
        """Background task for deviation monitoring."""
        while self._running:
            try:
                await self._monitor_deviations()

                # Monitor more frequently than baseline updates
                await asyncio.sleep(60.0)  # Check every minute

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in deviation monitoring: {e}")
                await asyncio.sleep(60.0)

    async def _perform_baseline_analysis(self) -> None:
        """Perform baseline analysis for all metric types."""
        current_time = time.time()
        update_interval = self.settings.baseline_update_interval_hours * 3600

        for metric_type, data_points in self._baseline_data.items():
            if len(data_points) < self._get_minimum_samples_for_baseline():
                continue

            last_update = self._last_baseline_update.get(metric_type, 0)
            if current_time - last_update >= update_interval:
                self._update_baseline(metric_type)

        self._benchmark_stats["analysis_cycles"] += 1

    async def _monitor_deviations(self) -> None:
        """Monitor for performance deviations."""
        # This would typically be called by the telemetry collector
        # when new metrics are collected. For now, we'll just update
        # the monitoring statistics.

        current_time = time.time()

        # Clean up old deviation alerts
        for metric_type, alerts in self._deviation_alerts.items():
            # Remove alerts older than 24 hours
            cutoff_time = current_time - 86400
            self._deviation_alerts[metric_type] = [
                alert for alert in alerts if alert["timestamp"] >= cutoff_time
            ]
