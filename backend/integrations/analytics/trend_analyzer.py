"""
Performance Trend Analysis Engine

Statistical analysis of performance trends with predictive capabilities.
Provides linear regression analysis, trend detection, and performance forecasting.
"""

import asyncio
import logging
import statistics
import time
from collections import defaultdict, deque
from typing import Any

from backend.integrations.analytics.config import PerformanceAnalyticsSettings
from backend.integrations.analytics.models import (
    MetricType,
    PerformanceMetric,
    PerformanceTrend,
    TrendDirection,
)

logger = logging.getLogger(__name__)


class TrendAnalyzer:
    """
    Performance trend analysis engine for statistical trend detection and prediction.

    Provides capabilities for:
    - Linear regression analysis of performance metrics
    - Trend direction classification (improving, stable, degrading, volatile)
    - Performance prediction with confidence intervals
    - Statistical significance testing
    """

    def __init__(self, settings: PerformanceAnalyticsSettings):
        """Initialize the trend analyzer."""
        self.settings = settings

        # Trend analysis data
        self._trend_data: dict[MetricType, deque] = defaultdict(lambda: deque(maxlen=10000))
        self._calculated_trends: dict[MetricType, PerformanceTrend] = {}

        # Analysis parameters
        self._trend_window_seconds = self.settings.trend_analysis_window_hours * 3600
        self._minimum_samples = self.settings.minimum_trend_samples

        # Background tasks
        self._analysis_tasks: list[asyncio.Task] = []
        self._running = False

        # Analysis statistics
        self._trend_stats = {
            "trends_calculated": 0,
            "significant_trends": 0,
            "predictions_made": 0,
            "analysis_cycles": 0,
        }

        logger.info("Trend analyzer initialized")

    async def startup(self) -> None:
        """Start trend analysis tasks."""
        if not self.settings.enabled or not self.settings.enable_trend_analysis:
            logger.info("Trend analysis disabled")
            return

        self._running = True

        # Start trend analysis task
        analysis_task = asyncio.create_task(self._trend_analysis_loop())
        self._analysis_tasks.append(analysis_task)

        logger.info("Trend analyzer started")

    async def shutdown(self) -> None:
        """Shutdown trend analyzer."""
        self._running = False

        # Cancel all analysis tasks
        for task in self._analysis_tasks:
            if not task.done():
                task.cancel()

        # Wait for tasks to complete
        if self._analysis_tasks:
            await asyncio.gather(*self._analysis_tasks, return_exceptions=True)

        self._analysis_tasks.clear()
        logger.info("Trend analyzer shutdown complete")

    def record_metric_for_trend_analysis(self, metric: PerformanceMetric) -> None:
        """
        Record a metric for trend analysis.

        Args:
            metric: Performance metric to analyze
        """
        if not self.settings.enable_trend_analysis:
            return

        # Store as (timestamp, value) tuple for analysis
        data_point = (metric.timestamp, metric.value)
        self._trend_data[metric.metric_type].append(data_point)

    def get_trend(self, metric_type: MetricType) -> PerformanceTrend | None:
        """
        Get calculated trend for a metric type.

        Args:
            metric_type: Metric type to get trend for

        Returns:
            Performance trend or None if not available
        """
        return self._calculated_trends.get(metric_type)

    def get_all_trends(self) -> dict[MetricType, PerformanceTrend]:
        """Get all calculated trends."""
        return self._calculated_trends.copy()

    def calculate_trend_for_metric(self, metric_type: MetricType) -> PerformanceTrend | None:
        """
        Calculate trend for a specific metric type.

        Args:
            metric_type: Metric type to analyze

        Returns:
            Performance trend or None if insufficient data
        """
        data_points = self._trend_data.get(metric_type)
        if not data_points or len(data_points) < self._minimum_samples:
            return None

        # Filter data to trend analysis window
        current_time = time.time()
        cutoff_time = current_time - self._trend_window_seconds

        filtered_data = [(t, v) for t, v in data_points if t >= cutoff_time]
        if len(filtered_data) < self._minimum_samples:
            return None

        return self._perform_trend_analysis(metric_type, filtered_data)

    def predict_value(
        self, metric_type: MetricType, future_seconds: float
    ) -> tuple[float | None, tuple[float, float] | None]:
        """
        Predict future value for a metric.

        Args:
            metric_type: Metric type to predict
            future_seconds: Seconds into the future to predict

        Returns:
            Tuple of (predicted_value, confidence_interval) or (None, None)
        """
        trend = self._calculated_trends.get(metric_type)
        if not trend or trend.r_squared < self.settings.trend_significance_threshold:
            return None, None

        # Use linear prediction based on trend slope
        predicted_value = trend.mean + (trend.slope * future_seconds)

        # Calculate simple confidence interval based on standard deviation
        confidence_margin = 1.96 * trend.std_dev  # 95% confidence interval
        confidence_interval = (
            predicted_value - confidence_margin,
            predicted_value + confidence_margin,
        )

        self._trend_stats["predictions_made"] += 1

        return predicted_value, confidence_interval

    def get_trend_statistics(self) -> dict[str, Any]:
        """Get trend analysis statistics."""
        return {
            "enabled": self.settings.enabled and self.settings.enable_trend_analysis,
            "running": self._running,
            "trends_count": len(self._calculated_trends),
            "trend_metrics": [mt.value for mt in self._calculated_trends],
            "data_points": {mt.value: len(data) for mt, data in self._trend_data.items()},
            "statistics": self._trend_stats.copy(),
            "significant_trends": {
                mt.value: trend.direction.value
                for mt, trend in self._calculated_trends.items()
                if trend.r_squared >= self.settings.trend_significance_threshold
            },
        }

    # Internal analysis methods

    def _perform_trend_analysis(
        self, metric_type: MetricType, data_points: list[tuple[float, float]]
    ) -> PerformanceTrend:
        """
        Perform statistical trend analysis on data points.

        Args:
            metric_type: Metric type being analyzed
            data_points: List of (timestamp, value) tuples

        Returns:
            Performance trend analysis results
        """
        try:
            # Extract timestamps and values
            timestamps = [t for t, v in data_points]
            values = [v for t, v in data_points]

            # Normalize timestamps to start from 0
            min_timestamp = min(timestamps)
            normalized_times = [t - min_timestamp for t in timestamps]

            # Calculate linear regression
            slope, r_squared = self._calculate_linear_regression(normalized_times, values)

            # Calculate statistical properties
            mean_value = statistics.mean(values)
            std_dev = statistics.stdev(values) if len(values) > 1 else 0.0
            min_value = min(values)
            max_value = max(values)

            # Determine trend direction
            direction = self._classify_trend_direction(slope, r_squared, std_dev, mean_value)

            # Generate predictions
            predicted_1h, predicted_24h = self._generate_predictions(slope, mean_value)
            confidence_interval = self._calculate_confidence_interval(mean_value, std_dev)

            # Create trend object
            trend = PerformanceTrend(
                metric_type=metric_type,
                time_window_seconds=self._trend_window_seconds,
                direction=direction,
                slope=slope,
                r_squared=r_squared,
                mean=mean_value,
                std_dev=std_dev,
                min_value=min_value,
                max_value=max_value,
                predicted_value_1h=predicted_1h,
                predicted_value_24h=predicted_24h,
                confidence_interval=confidence_interval,
                data_points=data_points[-100:],  # Keep last 100 points for reference
            )

            # Store calculated trend
            self._calculated_trends[metric_type] = trend
            self._trend_stats["trends_calculated"] += 1

            if r_squared >= self.settings.trend_significance_threshold:
                self._trend_stats["significant_trends"] += 1

            logger.debug(
                f"Calculated trend for {metric_type.value}: "
                f"{direction.value} (slope: {slope:.4f}, r²: {r_squared:.3f})"
            )

            return trend

        except Exception as e:
            logger.error(f"Error performing trend analysis for {metric_type.value}: {e}")
            # Return a neutral trend on error
            return PerformanceTrend(
                metric_type=metric_type,
                time_window_seconds=self._trend_window_seconds,
                direction=TrendDirection.STABLE,
                slope=0.0,
            )

    def _calculate_linear_regression(
        self, x_values: list[float], y_values: list[float]
    ) -> tuple[float, float]:
        """
        Calculate linear regression slope and R-squared.

        Args:
            x_values: Independent variable values (time)
            y_values: Dependent variable values (metric values)

        Returns:
            Tuple of (slope, r_squared)
        """
        n = len(x_values)
        if n < 2:
            return 0.0, 0.0

        # Calculate means
        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(y_values)

        # Calculate slope and correlation
        numerator = sum(
            (x - x_mean) * (y - y_mean) for x, y in zip(x_values, y_values, strict=False)
        )
        x_variance = sum((x - x_mean) ** 2 for x in x_values)

        if x_variance == 0:
            return 0.0, 0.0

        slope = numerator / x_variance

        # Calculate R-squared
        y_variance = sum((y - y_mean) ** 2 for y in y_values)
        if y_variance == 0:
            r_squared = 1.0 if slope == 0 else 0.0
        else:
            ss_res = sum(
                (y - (y_mean + slope * (x - x_mean))) ** 2
                for x, y in zip(x_values, y_values, strict=False)
            )
            r_squared = 1 - (ss_res / y_variance)

        return slope, max(0.0, r_squared)  # Ensure R-squared is non-negative

    def _classify_trend_direction(
        self, slope: float, r_squared: float, std_dev: float, mean_value: float
    ) -> TrendDirection:
        """
        Classify trend direction based on statistical properties.

        Args:
            slope: Linear regression slope
            r_squared: Correlation coefficient
            std_dev: Standard deviation
            mean_value: Mean value

        Returns:
            Trend direction classification
        """
        # Check if trend is significant
        if r_squared < self.settings.trend_significance_threshold:
            # High volatility indicates volatile trend
            if mean_value > 0 and std_dev / mean_value > 0.5:  # Coefficient of variation > 50%
                return TrendDirection.VOLATILE
            return TrendDirection.STABLE

        # Classify based on slope
        slope_threshold = std_dev * 0.1  # 10% of std dev as threshold

        if slope > slope_threshold:
            return (
                TrendDirection.IMPROVING
                if self._is_improvement_positive(slope)
                else TrendDirection.DEGRADING
            )
        if slope < -slope_threshold:
            return (
                TrendDirection.DEGRADING
                if self._is_improvement_positive(slope)
                else TrendDirection.IMPROVING
            )
        return TrendDirection.STABLE

    def _is_improvement_positive(self, slope: float) -> bool:
        """
        Determine if a positive slope indicates improvement.

        For most metrics, higher values are worse (latency, CPU usage),
        but for some metrics, higher values are better (throughput).
        """
        # This could be made configurable per metric type
        # For now, assume positive slope is generally degradation
        return False

    def _generate_predictions(
        self, slope: float, mean_value: float
    ) -> tuple[float | None, float | None]:
        """
        Generate predictions for 1 hour and 24 hours.

        Args:
            slope: Trend slope per second
            mean_value: Current mean value

        Returns:
            Tuple of (1_hour_prediction, 24_hour_prediction)
        """
        try:
            # Predict based on linear trend
            predicted_1h = mean_value + (slope * 3600)  # 1 hour = 3600 seconds
            predicted_24h = mean_value + (slope * 86400)  # 24 hours = 86400 seconds

            return predicted_1h, predicted_24h

        except Exception:
            return None, None

    def _calculate_confidence_interval(
        self, mean_value: float, std_dev: float
    ) -> tuple[float, float]:
        """
        Calculate 95% confidence interval.

        Args:
            mean_value: Mean value
            std_dev: Standard deviation

        Returns:
            Tuple of (lower_bound, upper_bound)
        """
        margin = 1.96 * std_dev  # 95% confidence interval
        return (mean_value - margin, mean_value + margin)

    # Background analysis tasks

    async def _trend_analysis_loop(self) -> None:
        """Background task for periodic trend analysis."""
        while self._running:
            try:
                await self._perform_trend_analysis_cycle()

                # Sleep for analysis interval (quarter of trend window)
                sleep_time = self._trend_window_seconds / 4
                await asyncio.sleep(min(sleep_time, 3600))  # Max 1 hour sleep

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in trend analysis cycle: {e}")
                await asyncio.sleep(300.0)  # Wait 5 minutes on error

    async def _perform_trend_analysis_cycle(self) -> None:
        """Perform trend analysis for all metric types."""
        for metric_type in list(self._trend_data.keys()):
            if len(self._trend_data[metric_type]) >= self._minimum_samples:
                self.calculate_trend_for_metric(metric_type)

        self._trend_stats["analysis_cycles"] += 1

        # Clean up old data
        current_time = time.time()
        cutoff_time = current_time - (self._trend_window_seconds * 2)  # Keep 2x window

        for data_points in self._trend_data.values():
            # Remove old data points
            while data_points and data_points[0][0] < cutoff_time:
                data_points.popleft()
