"""
Predictive Maintenance Engine

Advanced predictive maintenance capabilities based on historical data,
performance patterns, and machine learning approaches for RV systems.
"""

import logging
import statistics
import time
from collections import defaultdict, deque
from typing import Any

from backend.integrations.diagnostics.config import AdvancedDiagnosticsSettings
from backend.integrations.diagnostics.models import (
    DiagnosticTroubleCode,
    MaintenancePrediction,
    MaintenanceUrgency,
    SystemType,
)

logger = logging.getLogger(__name__)


class PredictiveMaintenanceEngine:
    """
    Predictive maintenance engine for RV systems.

    Analyzes historical performance data, DTC patterns, and system behavior
    to predict maintenance needs and component failures.
    """

    def __init__(self, settings: AdvancedDiagnosticsSettings):
        """Initialize predictive maintenance engine."""
        self.settings = settings

        # Performance data storage
        self._performance_history: dict[SystemType, deque] = defaultdict(lambda: deque(maxlen=1000))

        # Component tracking
        self._component_health: dict[str, dict[str, Any]] = {}
        self._failure_patterns: dict[SystemType, list[dict[str, Any]]] = defaultdict(list)

        # Prediction cache
        self._predictions: dict[str, MaintenancePrediction] = {}
        self._last_analysis_time = 0.0

        logger.info("Predictive maintenance engine initialized")

    def record_performance_data(
        self,
        system_type: SystemType,
        component_name: str,
        metrics: dict[str, float],
        timestamp: float | None = None,
    ) -> None:
        """
        Record performance data for predictive analysis.

        Args:
            system_type: System type being measured
            component_name: Specific component name
            metrics: Performance metrics (e.g., temperature, pressure, voltage)
            timestamp: Optional timestamp (defaults to current time)
        """
        if timestamp is None:
            timestamp = time.time()

        performance_data = {
            "component": component_name,
            "timestamp": timestamp,
            "metrics": metrics.copy(),
        }

        self._performance_history[system_type].append(performance_data)

        # Update component health tracking
        component_key = f"{system_type.value}_{component_name}"
        if component_key not in self._component_health:
            self._component_health[component_key] = {
                "first_seen": timestamp,
                "last_update": timestamp,
                "total_measurements": 0,
                "baseline_metrics": {},
                "trend_analysis": {},
            }

        health_data = self._component_health[component_key]
        health_data["last_update"] = timestamp
        health_data["total_measurements"] += 1

        # Update baseline if this is early in component life
        if health_data["total_measurements"] <= 10:
            for metric, value in metrics.items():
                if metric not in health_data["baseline_metrics"]:
                    health_data["baseline_metrics"][metric] = []
                health_data["baseline_metrics"][metric].append(value)

                # Calculate baseline average after 10 measurements
                if len(health_data["baseline_metrics"][metric]) == 10:
                    health_data["baseline_metrics"][metric] = statistics.mean(
                        health_data["baseline_metrics"][metric]
                    )

    def record_dtc_pattern(
        self,
        system_type: SystemType,
        dtc: DiagnosticTroubleCode,
        preceding_conditions: dict[str, Any] | None = None,
    ) -> None:
        """
        Record DTC occurrence patterns for failure prediction.

        Args:
            system_type: System type where DTC occurred
            dtc: The diagnostic trouble code
            preceding_conditions: Conditions before DTC occurrence
        """
        pattern = {
            "dtc_code": dtc.code,
            "timestamp": dtc.first_occurrence,
            "severity": dtc.severity.value,
            "occurrence_count": dtc.occurrence_count,
            "preceding_conditions": preceding_conditions or {},
            "metadata": dtc.metadata,
        }

        self._failure_patterns[system_type].append(pattern)

        # Limit pattern history
        if len(self._failure_patterns[system_type]) > 100:
            self._failure_patterns[system_type] = self._failure_patterns[system_type][-100:]

    def analyze_component_wear(
        self, system_type: SystemType, component_name: str
    ) -> dict[str, Any]:
        """
        Analyze component wear patterns based on performance history.

        Args:
            system_type: System type to analyze
            component_name: Component name to analyze

        Returns:
            Wear analysis results
        """
        component_key = f"{system_type.value}_{component_name}"
        health_data = self._component_health.get(component_key, {})

        if (
            not health_data
            or health_data["total_measurements"] < self.settings.trend_analysis_minimum_samples
        ):
            return {
                "status": "insufficient_data",
                "measurements": health_data.get("total_measurements", 0),
                "required": self.settings.trend_analysis_minimum_samples,
            }

        # Get recent performance data
        recent_data = [
            data
            for data in self._performance_history[system_type]
            if data["component"] == component_name
        ]

        if len(recent_data) < self.settings.trend_analysis_minimum_samples:
            return {"status": "insufficient_recent_data"}

        # Analyze trends
        wear_analysis = {
            "component": component_name,
            "system_type": system_type.value,
            "analysis_timestamp": time.time(),
            "data_points": len(recent_data),
            "trends": {},
            "wear_indicators": [],
            "degradation_rate": 0.0,
            "time_span_days": 0.0,
        }

        if recent_data:
            time_span = recent_data[-1]["timestamp"] - recent_data[0]["timestamp"]
            wear_analysis["time_span_days"] = time_span / 86400.0  # Convert to days

            # Analyze each metric
            baseline_metrics = health_data.get("baseline_metrics", {})
            for metric in baseline_metrics:
                metric_values = [
                    data["metrics"].get(metric, 0)
                    for data in recent_data
                    if metric in data["metrics"]
                ]

                if len(metric_values) >= self.settings.trend_analysis_minimum_samples:
                    trend_analysis = self._analyze_metric_trend(
                        metric, metric_values, baseline_metrics[metric]
                    )
                    wear_analysis["trends"][metric] = trend_analysis

                    # Check for wear indicators
                    if trend_analysis["degradation_percentage"] > 10.0:
                        wear_analysis["wear_indicators"].append(
                            f"{metric}: {trend_analysis['degradation_percentage']:.1f}% degradation"
                        )

            # Calculate overall degradation rate
            degradation_rates = [
                trend["degradation_percentage"]
                for trend in wear_analysis["trends"].values()
                if trend["degradation_percentage"] > 0
            ]

            if degradation_rates:
                wear_analysis["degradation_rate"] = statistics.mean(degradation_rates)

        return wear_analysis

    def predict_failure_probability(
        self, system_type: SystemType, component_name: str, prediction_horizon_days: int = 30
    ) -> MaintenancePrediction:
        """
        Predict probability of component failure within specified time horizon.

        Args:
            system_type: System type to analyze
            component_name: Component name
            prediction_horizon_days: Prediction time horizon in days

        Returns:
            Maintenance prediction
        """
        # Analyze component wear
        wear_analysis = self.analyze_component_wear(system_type, component_name)

        # Initialize prediction
        prediction = MaintenancePrediction(
            system_type=system_type,
            component_name=component_name,
            confidence=0.0,
            urgency=MaintenanceUrgency.MONITOR,
        )

        if wear_analysis.get("status") != "insufficient_data":
            # Calculate failure probability based on wear analysis
            degradation_rate = wear_analysis.get("degradation_rate", 0.0)
            wear_indicators = len(wear_analysis.get("wear_indicators", []))

            # Simple failure prediction model
            failure_probability = self._calculate_failure_probability(
                degradation_rate, wear_indicators, prediction_horizon_days
            )

            prediction.confidence = min(1.0, failure_probability)

            # Determine urgency based on probability and degradation
            if failure_probability > 0.8 or degradation_rate > 50.0:
                prediction.urgency = MaintenanceUrgency.IMMEDIATE
                prediction.predicted_failure_date = time.time() + (7 * 86400)  # 7 days
            elif failure_probability > 0.6 or degradation_rate > 30.0:
                prediction.urgency = MaintenanceUrgency.URGENT
                prediction.predicted_failure_date = time.time() + (14 * 86400)  # 14 days
            elif failure_probability > 0.4 or degradation_rate > 15.0:
                prediction.urgency = MaintenanceUrgency.SOON
                prediction.predicted_failure_date = time.time() + (30 * 86400)  # 30 days
            elif failure_probability > 0.2 or degradation_rate > 5.0:
                prediction.urgency = MaintenanceUrgency.SCHEDULED

            # Add analysis details
            prediction.trend_analysis = wear_analysis
            prediction.performance_degradation = {
                trend_name: trend["degradation_percentage"]
                for trend_name, trend in wear_analysis.get("trends", {}).items()
            }

            # Generate recommendations
            prediction.recommended_actions = self._generate_maintenance_recommendations(
                system_type, component_name, wear_analysis, failure_probability
            )

        # Cache prediction
        prediction_key = f"{system_type.value}_{component_name}"
        self._predictions[prediction_key] = prediction

        return prediction

    def get_maintenance_schedule(self, time_horizon_days: int = 90) -> list[MaintenancePrediction]:
        """
        Generate optimized maintenance schedule for all components.

        Args:
            time_horizon_days: Planning horizon in days

        Returns:
            List of maintenance predictions sorted by urgency
        """
        predictions = []

        # Analyze all tracked components
        for component_key, health_data in self._component_health.items():
            if health_data["total_measurements"] < self.settings.trend_analysis_minimum_samples:
                continue

            # Parse component key
            parts = component_key.split("_", 1)
            if len(parts) != 2:
                continue

            try:
                system_type = SystemType(parts[0])
                component_name = parts[1]

                prediction = self.predict_failure_probability(
                    system_type, component_name, time_horizon_days
                )

                if prediction.confidence >= self.settings.prediction_confidence_threshold:
                    predictions.append(prediction)

            except ValueError:
                continue  # Invalid system type

        # Sort by urgency and confidence
        urgency_order = {
            MaintenanceUrgency.IMMEDIATE: 0,
            MaintenanceUrgency.URGENT: 1,
            MaintenanceUrgency.SOON: 2,
            MaintenanceUrgency.SCHEDULED: 3,
            MaintenanceUrgency.MONITOR: 4,
        }

        predictions.sort(key=lambda p: (urgency_order[p.urgency], -p.confidence))

        return predictions

    def get_prediction_statistics(self) -> dict[str, Any]:
        """Get predictive maintenance statistics."""
        total_components = len(self._component_health)
        components_with_data = sum(
            1
            for health in self._component_health.values()
            if health["total_measurements"] >= self.settings.trend_analysis_minimum_samples
        )

        active_predictions = len(
            [
                p
                for p in self._predictions.values()
                if p.confidence >= self.settings.prediction_confidence_threshold
            ]
        )

        return {
            "total_components_tracked": total_components,
            "components_with_sufficient_data": components_with_data,
            "active_predictions": active_predictions,
            "cached_predictions": len(self._predictions),
            "failure_patterns_recorded": sum(
                len(patterns) for patterns in self._failure_patterns.values()
            ),
            "performance_data_points": sum(
                len(history) for history in self._performance_history.values()
            ),
            "last_analysis_time": self._last_analysis_time,
        }

    # Internal helper methods

    def _analyze_metric_trend(
        self, metric_name: str, values: list[float], baseline: float
    ) -> dict[str, Any]:
        """Analyze trend for a specific metric."""
        if not values or baseline == 0:
            return {
                "metric": metric_name,
                "trend": "stable",
                "degradation_percentage": 0.0,
                "slope": 0.0,
                "confidence": 0.0,
            }

        # Calculate linear regression for trend
        n = len(values)
        x_values = list(range(n))

        # Simple linear regression
        x_mean = statistics.mean(x_values)
        y_mean = statistics.mean(values)

        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_values, values, strict=False))
        denominator = sum((x - x_mean) ** 2 for x in x_values)

        slope = numerator / denominator if denominator != 0 else 0.0

        # Calculate trend direction
        current_value = values[-1]
        degradation_percentage = abs(current_value - baseline) / baseline * 100

        trend = "stable"
        if abs(slope) > 0.1:  # Significant trend
            if (metric_name.lower() in ["temperature", "pressure", "vibration"] and slope > 0) or (
                metric_name.lower() in ["voltage", "efficiency"] and slope < 0
            ):
                trend = "degrading"
            elif (
                metric_name.lower() in ["temperature", "pressure", "vibration"] and slope < 0
            ) or (metric_name.lower() in ["voltage", "efficiency"] and slope > 0):
                trend = "improving"

        # Calculate confidence based on data consistency
        variance = statistics.variance(values) if len(values) > 1 else 0
        confidence = max(0.0, min(1.0, 1.0 - (variance / (y_mean**2))))

        return {
            "metric": metric_name,
            "trend": trend,
            "degradation_percentage": degradation_percentage,
            "slope": slope,
            "confidence": confidence,
            "current_value": current_value,
            "baseline_value": baseline,
            "data_points": n,
        }

    def _calculate_failure_probability(
        self, degradation_rate: float, wear_indicator_count: int, horizon_days: int
    ) -> float:
        """Calculate failure probability based on analysis results."""
        # Simple heuristic model for failure probability
        base_probability = 0.1  # 10% base probability

        # Add probability based on degradation rate
        degradation_factor = min(0.5, degradation_rate / 100.0)

        # Add probability based on wear indicators
        wear_factor = min(0.3, wear_indicator_count * 0.1)

        # Adjust for time horizon (longer horizon = higher probability)
        time_factor = min(0.2, horizon_days / 365.0)

        total_probability = base_probability + degradation_factor + wear_factor + time_factor

        return min(1.0, total_probability)

    def _generate_maintenance_recommendations(
        self,
        system_type: SystemType,
        component_name: str,
        wear_analysis: dict[str, Any],
        failure_probability: float,
    ) -> list[str]:
        """Generate maintenance recommendations based on analysis."""
        recommendations = []

        # System-specific recommendations
        if system_type == SystemType.ENGINE:
            recommendations.extend(
                [
                    "Check engine oil level and condition",
                    "Inspect air filter condition",
                    "Verify cooling system operation",
                    "Monitor exhaust system",
                ]
            )
        elif system_type == SystemType.ELECTRICAL:
            recommendations.extend(
                [
                    "Check battery voltage and connections",
                    "Inspect wiring for corrosion",
                    "Test charging system operation",
                    "Verify ground connections",
                ]
            )
        elif system_type == SystemType.BRAKES:
            recommendations.extend(
                [
                    "Inspect brake pads/shoes for wear",
                    "Check brake fluid level and condition",
                    "Test brake system pressure",
                    "Verify brake component operation",
                ]
            )

        # Add specific recommendations based on wear analysis
        wear_indicators = wear_analysis.get("wear_indicators", [])
        if wear_indicators:
            recommendations.append(f"Address wear indicators: {', '.join(wear_indicators)}")

        # Add urgency-based recommendations
        if failure_probability > 0.8:
            recommendations.insert(0, "URGENT: Schedule immediate inspection and service")
        elif failure_probability > 0.6:
            recommendations.insert(0, "Schedule service within 2 weeks")
        elif failure_probability > 0.4:
            recommendations.insert(0, "Plan service within next month")

        return recommendations
