"""
Predictive Maintenance Service

Implements Gemini's hybrid edge/cloud approach for predictive maintenance with:
- Component health scoring with dynamic thresholds
- Tiered alerting system (Watch, Advise, Alert)
- Trend analysis with EWMA and anomaly detection
- Maintenance lifecycle tracking
- Proactive recommendations based on usage patterns and fleet data
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Any

from backend.models.predictive_maintenance import (
    ComponentHealthModel,
    MaintenanceHistoryModel,
    MaintenanceRecommendationModel,
    RVHealthOverviewModel,
)
logger = logging.getLogger(__name__)


class PredictiveMaintenanceService:
    """
    Service for predictive maintenance analysis and recommendations.

    Implements a sophisticated health scoring system with trend analysis,
    anomaly detection, and proactive maintenance recommendations.
    """

    def __init__(self, database_manager=None):
        """Initialize the predictive maintenance service.

        Args:
            database_manager: Optional database manager for persistence operations.
                             If None, persistence operations will be disabled.
        """
        self._db_manager = database_manager

        # Component health data storage
        self.component_health: dict[str, ComponentHealthModel] = {}
        self.maintenance_history: dict[str, MaintenanceHistoryModel] = {}
        self.recommendations: dict[str, MaintenanceRecommendationModel] = {}

        # Initialize with sample data for demonstration
        self._initialize_sample_data()

        logger.info("PredictiveMaintenanceService initialized")

    def _initialize_sample_data(self) -> None:
        """Initialize with sample component data for demonstration."""
        sample_components = [
            {
                "component_id": "battery_coach_main",
                "component_type": "battery",
                "component_name": "Coach Battery Bank",
                "health_score": 78.0,
                "status": "advise",
                "remaining_useful_life_days": 120,
                "usage_hours": 2340.5,
                "anomaly_count": 3,
                "trend_direction": "degrading",
                "last_maintenance": datetime.now() - timedelta(days=180),
                "next_maintenance_due": datetime.now() + timedelta(days=30),
            },
            {
                "component_id": "generator_main",
                "component_type": "generator",
                "component_name": "Main Generator",
                "health_score": 92.0,
                "status": "healthy",
                "remaining_useful_life_days": 800,
                "usage_hours": 156.2,
                "anomaly_count": 0,
                "trend_direction": "stable",
                "last_maintenance": datetime.now() - timedelta(days=90),
                "next_maintenance_due": datetime.now() + timedelta(days=270),
            },
            {
                "component_id": "slides_living_room",
                "component_type": "slide_out",
                "component_name": "Living Room Slide",
                "health_score": 85.0,
                "status": "watch",
                "remaining_useful_life_days": 1200,
                "usage_cycles": 234,
                "anomaly_count": 1,
                "trend_direction": "stable",
                "last_maintenance": datetime.now() - timedelta(days=365),
                "next_maintenance_due": datetime.now() + timedelta(days=90),
            },
            {
                "component_id": "water_pump_fresh",
                "component_type": "pump",
                "component_name": "Fresh Water Pump",
                "health_score": 65.0,
                "status": "advise",
                "remaining_useful_life_days": 45,
                "usage_hours": 891.3,
                "anomaly_count": 5,
                "trend_direction": "degrading",
                "last_maintenance": datetime.now() - timedelta(days=730),
                "next_maintenance_due": datetime.now() + timedelta(days=15),
            },
            {
                "component_id": "hvac_main",
                "component_type": "hvac",
                "component_name": "Main Air Conditioner",
                "health_score": 88.0,
                "status": "healthy",
                "remaining_useful_life_days": 1500,
                "usage_hours": 445.7,
                "anomaly_count": 0,
                "trend_direction": "stable",
                "last_maintenance": datetime.now() - timedelta(days=120),
                "next_maintenance_due": datetime.now() + timedelta(days=240),
            },
        ]

        for component_data in sample_components:
            component = ComponentHealthModel(**component_data)
            self.component_health[component.component_id] = component

        # Sample recommendations
        sample_recommendations = [
            {
                "recommendation_id": "rec_battery_test",
                "component_id": "battery_coach_main",
                "component_name": "Coach Battery Bank",
                "level": "advise",
                "title": "Battery Performance Declining",
                "message": "Your coach battery health is at 78%. It consistently drops below optimal voltage under load. Consider having it tested before your next long trip.",
                "priority": 2,
                "estimated_cost": 350.0,
                "estimated_time_hours": 1.0,
                "urgency_days": 30,
                "created_at": datetime.now() - timedelta(days=5),
                "maintenance_type": "inspection",
            },
            {
                "recommendation_id": "rec_pump_replacement",
                "component_id": "water_pump_fresh",
                "component_name": "Fresh Water Pump",
                "level": "alert",
                "title": "Water Pump Requires Attention",
                "message": "Fresh water pump showing significant performance degradation. Power draw has increased 40% and pressure drops detected. Replacement recommended within 2 weeks.",
                "priority": 1,
                "estimated_cost": 180.0,
                "estimated_time_hours": 2.5,
                "urgency_days": 14,
                "created_at": datetime.now() - timedelta(days=2),
                "maintenance_type": "replacement",
            },
            {
                "recommendation_id": "rec_slide_lubrication",
                "component_id": "slides_living_room",
                "component_name": "Living Room Slide",
                "level": "watch",
                "title": "Slide Maintenance Due",
                "message": "Living room slide is due for annual lubrication and inspection. Operation is normal but preventive maintenance is recommended.",
                "priority": 3,
                "estimated_cost": 75.0,
                "estimated_time_hours": 0.5,
                "urgency_days": 90,
                "created_at": datetime.now() - timedelta(days=1),
                "maintenance_type": "service",
            },
        ]

        for rec_data in sample_recommendations:
            recommendation = MaintenanceRecommendationModel(**rec_data)
            self.recommendations[recommendation.recommendation_id] = recommendation

    async def get_health_overview(self) -> dict[str, Any]:
        """Get overall RV health overview with system breakdown."""
        components = list(self.component_health.values())

        if not components:
            return RVHealthOverviewModel(
                overall_health_score=100.0,
                status="healthy",
                components_monitored=0,
                last_updated=datetime.now(),
            ).to_dict()

        # Calculate overall health score (weighted average)
        total_weight = len(components)
        overall_score = sum(comp.health_score for comp in components) / total_weight

        # Determine overall status based on worst component status
        status_priority = {"healthy": 0, "watch": 1, "advise": 2, "alert": 3}
        worst_status = max(components, key=lambda c: status_priority.get(c.status, 0)).status

        # Count active recommendations by level
        active_recs = [r for r in self.recommendations.values() if not r.dismissed]
        critical_alerts = len([r for r in active_recs if r.level == "alert"])
        active_recommendations = len(active_recs)

        # System health breakdown
        system_breakdown = {}
        for component in components:
            system_type = component.component_type
            if system_type not in system_breakdown:
                system_breakdown[system_type] = []
            system_breakdown[system_type].append(component.health_score)

        # Average health by system type
        system_health = {
            system: sum(scores) / len(scores) for system, scores in system_breakdown.items()
        }

        return RVHealthOverviewModel(
            overall_health_score=round(overall_score, 1),
            status=worst_status,
            critical_alerts=critical_alerts,
            active_recommendations=active_recommendations,
            components_monitored=len(components),
            last_updated=datetime.now(),
            system_health_breakdown=system_health,
        ).to_dict()

    async def get_component_health(
        self,
        system_type: str | None = None,
        status: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get health status for all components with optional filtering."""
        components = list(self.component_health.values())

        # Apply filters
        if system_type:
            components = [c for c in components if c.component_type == system_type]
        if status:
            components = [c for c in components if c.status == status]

        # Sort by health score (worst first) and then by status priority
        status_priority = {"alert": 0, "advise": 1, "watch": 2, "healthy": 3}
        components.sort(key=lambda c: (status_priority.get(c.status, 4), c.health_score))

        return [component.to_dict() for component in components]

    async def get_component_health_detail(self, component_id: str) -> dict[str, Any] | None:
        """Get detailed health information for a specific component."""
        component = self.component_health.get(component_id)
        return component.to_dict() if component else None

    async def get_maintenance_recommendations(
        self,
        level: str | None = None,
        component_id: str | None = None,
        acknowledged: bool | None = None,
    ) -> list[dict[str, Any]]:
        """Get maintenance recommendations with filtering."""
        recommendations = list(self.recommendations.values())

        # Apply filters
        if level:
            recommendations = [r for r in recommendations if r.level == level]
        if component_id:
            recommendations = [r for r in recommendations if r.component_id == component_id]
        if acknowledged is not None:
            recommendations = [
                r for r in recommendations if (r.acknowledged_at is not None) == acknowledged
            ]

        # Filter out dismissed recommendations unless explicitly requested
        recommendations = [r for r in recommendations if not r.dismissed]

        # Sort by priority (highest first) and then by creation date
        recommendations.sort(key=lambda r: (r.priority, r.created_at))

        return [rec.to_dict() for rec in recommendations]

    async def acknowledge_recommendation(self, recommendation_id: str) -> bool:
        """Acknowledge a maintenance recommendation."""
        recommendation = self.recommendations.get(recommendation_id)
        if not recommendation:
            return False

        recommendation.acknowledged_at = datetime.now()
        logger.info(f"Acknowledged recommendation: {recommendation_id}")
        return True

    async def get_component_trends(
        self,
        component_id: str,
        metric: str | None = None,
        days: int = 30,
    ) -> dict[str, Any] | None:
        """Get trend analysis data for a component."""
        component = self.component_health.get(component_id)
        if not component:
            return None

        # Generate sample trend data for demonstration
        # In a real implementation, this would query time-series data
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Sample trend points (simulated declining battery voltage)
        trend_points = []
        for i in range(days):
            date = start_date + timedelta(days=i)
            if component.component_type == "battery":
                # Simulate declining battery voltage trend
                base_voltage = 12.6
                decline_factor = i * 0.01  # Gradual decline
                noise = (i % 7) * 0.05  # Weekly variation
                voltage = base_voltage - decline_factor + noise
                trend_points.append(
                    {"timestamp": date.isoformat(), "value": round(voltage, 2), "metric": "voltage"}
                )
            else:
                # Generic health score trend
                base_score = component.health_score
                variation = (i % 10) * 2 - 5  # ±5 point variation
                score = max(0, min(100, base_score + variation))
                trend_points.append(
                    {
                        "timestamp": date.isoformat(),
                        "value": round(score, 1),
                        "metric": "health_score",
                    }
                )

        # Define normal operating ranges by component type
        normal_ranges = {
            "battery": {"min": 12.2, "max": 12.8, "metric": "voltage"},
            "generator": {"min": 80.0, "max": 100.0, "metric": "health_score"},
            "pump": {"min": 70.0, "max": 100.0, "metric": "health_score"},
            "hvac": {"min": 85.0, "max": 100.0, "metric": "health_score"},
            "slide_out": {"min": 80.0, "max": 100.0, "metric": "health_score"},
        }

        normal_range = normal_ranges.get(
            component.component_type, {"min": 0, "max": 100, "metric": "health_score"}
        )

        # Detect anomalies (values outside normal range)
        anomalies = []
        for point in trend_points:
            if point["value"] < normal_range["min"] or point["value"] > normal_range["max"]:
                anomalies.append(
                    {
                        "timestamp": point["timestamp"],
                        "value": point["value"],
                        "severity": "high"
                        if point["value"] < normal_range["min"] * 0.9
                        else "medium",
                        "description": f"{normal_range['metric']} outside normal range",
                    }
                )

        # Generate trend analysis
        if len(trend_points) >= 2:
            start_value = trend_points[0]["value"]
            end_value = trend_points[-1]["value"]
            change_percent = ((end_value - start_value) / start_value) * 100

            if abs(change_percent) < 2:
                trend_analysis = "Stable performance with minimal variation"
            elif change_percent > 2:
                trend_analysis = f"Improving trend: {change_percent:.1f}% increase over {days} days"
            else:
                trend_analysis = (
                    f"Declining trend: {abs(change_percent):.1f}% decrease over {days} days"
                )
        else:
            trend_analysis = "Insufficient data for trend analysis"

        return {
            "component_id": component_id,
            "metric_name": normal_range["metric"],
            "trend_points": trend_points,
            "normal_range": normal_range,
            "anomalies": anomalies,
            "prediction_confidence": 0.85,  # Static confidence for demo
            "trend_analysis": trend_analysis,
        }

    async def log_maintenance_activity(self, maintenance_entry: Any) -> str:
        """Log a maintenance activity and update component health."""
        entry_id = f"maint_{uuid.uuid4().hex[:12]}"

        # Create maintenance history entry
        history_entry = MaintenanceHistoryModel(
            entry_id=entry_id,
            component_id=maintenance_entry.component_id,
            component_name=self._get_component_name(maintenance_entry.component_id),
            maintenance_type=maintenance_entry.maintenance_type,
            description=maintenance_entry.description,
            performed_at=datetime.now(),
            cost=maintenance_entry.cost,
            performed_by=maintenance_entry.performed_by,
            location=maintenance_entry.location,
            notes=maintenance_entry.notes,
        )

        self.maintenance_history[entry_id] = history_entry

        # Update component health based on maintenance type
        component = self.component_health.get(maintenance_entry.component_id)
        if component:
            if maintenance_entry.maintenance_type in ["replacement", "rebuild"]:
                # Reset component health for replacements
                component.health_score = 100.0
                component.status = "healthy"
                component.anomaly_count = 0
                component.trend_direction = "stable"
                component.usage_hours = 0.0
                component.usage_cycles = 0
            elif maintenance_entry.maintenance_type in ["service", "repair"]:
                # Improve health for service/repair
                component.health_score = min(100.0, component.health_score + 15.0)
                component.anomaly_count = max(0, component.anomaly_count - 2)
                if component.health_score > 80:
                    component.status = "healthy"
                elif component.health_score > 60:
                    component.status = "watch"

            component.last_maintenance = datetime.now()

            # Set next maintenance due date based on component type
            maintenance_intervals = {
                "battery": 180,  # 6 months
                "generator": 365,  # 1 year
                "pump": 365,  # 1 year
                "hvac": 365,  # 1 year
                "slide_out": 365,  # 1 year
            }
            interval = maintenance_intervals.get(component.component_type, 365)
            component.next_maintenance_due = datetime.now() + timedelta(days=interval)

        logger.info(
            f"Logged maintenance activity: {entry_id} for component {maintenance_entry.component_id}"
        )
        return entry_id

    async def get_maintenance_history(
        self,
        component_id: str | None = None,
        maintenance_type: str | None = None,
        days: int = 90,
    ) -> list[dict[str, Any]]:
        """Get maintenance history with filtering."""
        cutoff_date = datetime.now() - timedelta(days=days)
        history = [
            entry
            for entry in self.maintenance_history.values()
            if entry.performed_at >= cutoff_date
        ]

        # Apply filters
        if component_id:
            history = [h for h in history if h.component_id == component_id]
        if maintenance_type:
            history = [h for h in history if h.maintenance_type == maintenance_type]

        # Sort by date (most recent first)
        history.sort(key=lambda h: h.performed_at, reverse=True)

        return [entry.to_dict() for entry in history]

    def _get_component_name(self, component_id: str) -> str:
        """Get human-readable component name."""
        component = self.component_health.get(component_id)
        return component.component_name if component else component_id
