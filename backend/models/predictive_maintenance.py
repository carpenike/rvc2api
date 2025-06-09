"""
Predictive Maintenance Models

Pydantic models for predictive maintenance components, health tracking,
and maintenance recommendations.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ComponentHealthModel(BaseModel):
    """Model for component health tracking."""

    component_id: str = Field(..., description="Component identifier")
    component_type: str = Field(..., description="Type of component")
    component_name: str = Field(..., description="Human-readable component name")
    health_score: float = Field(..., ge=0, le=100, description="Health score (0-100%)")
    status: str = Field(..., description="Health status (healthy, watch, advise, alert)")
    remaining_useful_life_days: int | None = Field(
        None, description="Estimated days until replacement needed"
    )
    last_maintenance: datetime | None = Field(None, description="Last maintenance date")
    next_maintenance_due: datetime | None = Field(None, description="Next scheduled maintenance")
    usage_hours: float | None = Field(None, description="Total usage hours")
    usage_cycles: int | None = Field(None, description="Total usage cycles")
    anomaly_count: int = Field(default=0, description="Recent anomaly count")
    trend_direction: str = Field(
        default="stable", description="Trend direction (improving, stable, degrading)"
    )
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return self.model_dump()


class RVHealthOverviewModel(BaseModel):
    """Model for overall RV health overview."""

    overall_health_score: float = Field(..., ge=0, le=100, description="Overall health score")
    status: str = Field(..., description="Overall status (healthy, watch, advise, alert)")
    critical_alerts: int = Field(default=0, description="Number of critical alerts")
    active_recommendations: int = Field(default=0, description="Number of active recommendations")
    components_monitored: int = Field(default=0, description="Total components being monitored")
    last_updated: datetime = Field(..., description="Last update timestamp")
    system_health_breakdown: dict[str, float] = Field(
        default_factory=dict, description="Health by system type"
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return self.model_dump()


class MaintenanceRecommendationModel(BaseModel):
    """Model for maintenance recommendations."""

    recommendation_id: str = Field(..., description="Unique recommendation identifier")
    component_id: str = Field(..., description="Component identifier")
    component_name: str = Field(..., description="Human-readable component name")
    level: str = Field(..., description="Recommendation level (watch, advise, alert)")
    title: str = Field(..., description="Recommendation title")
    message: str = Field(..., description="Detailed recommendation message")
    priority: int = Field(..., ge=1, le=5, description="Priority level (1=highest, 5=lowest)")
    estimated_cost: float | None = Field(None, description="Estimated maintenance cost")
    estimated_time_hours: float | None = Field(None, description="Estimated time required")
    urgency_days: int | None = Field(None, description="Days until urgent")
    created_at: datetime = Field(..., description="Recommendation creation time")
    acknowledged_at: datetime | None = Field(None, description="Acknowledgment timestamp")
    dismissed: bool = Field(default=False, description="Whether recommendation was dismissed")
    maintenance_type: str = Field(
        default="inspection", description="Type of maintenance (inspection, service, replacement)"
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return self.model_dump()


class MaintenanceHistoryModel(BaseModel):
    """Model for maintenance history entries."""

    entry_id: str = Field(..., description="History entry identifier")
    component_id: str = Field(..., description="Component identifier")
    component_name: str = Field(..., description="Component name")
    maintenance_type: str = Field(..., description="Type of maintenance")
    description: str = Field(..., description="Maintenance description")
    performed_at: datetime = Field(..., description="When maintenance was performed")
    cost: float | None = Field(None, description="Maintenance cost")
    performed_by: str | None = Field(None, description="Who performed maintenance")
    location: str | None = Field(None, description="Maintenance location")
    notes: str | None = Field(None, description="Additional notes")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return self.model_dump()
