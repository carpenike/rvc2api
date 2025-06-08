"""
Advanced Diagnostics Data Models

Unified data models for diagnostic information across all protocols and systems.
"""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class DTCSeverity(Enum):
    """Diagnostic trouble code severity levels."""

    CRITICAL = "critical"  # Immediate attention required
    HIGH = "high"  # Service required soon
    MEDIUM = "medium"  # Monitor and plan service
    LOW = "low"  # Informational
    INFORMATIONAL = "info"  # System status, not a fault


class SystemType(Enum):
    """System types across all protocols."""

    # RV-C Systems
    LIGHTING = "lighting"
    CLIMATE = "climate"
    POWER = "power"
    TANKS = "tanks"
    SLIDES = "slides"
    AWNINGS = "awnings"
    LEVELING = "leveling"

    # J1939 Systems
    ENGINE = "engine"
    TRANSMISSION = "transmission"
    BRAKES = "brakes"
    SUSPENSION = "suspension"
    STEERING = "steering"
    CHASSIS = "chassis"

    # Cross-System
    ELECTRICAL = "electrical"
    HYDRAULIC = "hydraulic"
    PNEUMATIC = "pneumatic"
    SAFETY = "safety"
    COMMUNICATIONS = "communications"
    UNKNOWN = "unknown"


class ProtocolType(Enum):
    """Protocol types for diagnostic source identification."""

    RVC = "rvc"
    J1939 = "j1939"
    FIREFLY = "firefly"
    SPARTAN_K2 = "spartan_k2"
    PROPRIETARY = "proprietary"
    UNKNOWN = "unknown"


class MaintenanceUrgency(Enum):
    """Maintenance urgency levels."""

    IMMEDIATE = "immediate"  # Stop operation immediately
    URGENT = "urgent"  # Service within 24 hours
    SOON = "soon"  # Service within 1 week
    SCHEDULED = "scheduled"  # Service at next interval
    MONITOR = "monitor"  # Continue monitoring


@dataclass
class DiagnosticTroubleCode:
    """Comprehensive DTC representation across all protocols."""

    # Basic DTC information
    code: int  # Numeric DTC code
    protocol: ProtocolType  # Source protocol
    system_type: SystemType  # Affected system
    severity: DTCSeverity  # Severity level

    # Timing information
    first_occurrence: float = field(default_factory=time.time)
    last_occurrence: float = field(default_factory=time.time)
    occurrence_count: int = 1

    # Context information
    source_address: int | None = None  # Source address from CAN
    pgn: int | None = None  # PGN for J1939
    dgn: int | None = None  # DGN for RV-C
    raw_data: bytes | None = None  # Raw message data

    # Descriptive information
    description: str = ""  # Human-readable description
    possible_causes: list[str] = field(default_factory=list)
    recommended_actions: list[str] = field(default_factory=list)

    # Status tracking
    active: bool = True  # Currently active
    intermittent: bool = False  # Intermittent fault
    resolved: bool = False  # Fault resolved
    acknowledged: bool = False  # Acknowledged by user

    # Additional metadata
    metadata: dict[str, Any] = field(default_factory=dict)

    def update_occurrence(self) -> None:
        """Update occurrence tracking when DTC is seen again."""
        self.last_occurrence = time.time()
        self.occurrence_count += 1
        if self.occurrence_count > 1:
            self.intermittent = True

    def resolve(self) -> None:
        """Mark DTC as resolved."""
        self.resolved = True
        self.active = False

    def acknowledge(self) -> None:
        """Acknowledge DTC."""
        self.acknowledged = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "code": self.code,
            "protocol": self.protocol.value,
            "system_type": self.system_type.value,
            "severity": self.severity.value,
            "first_occurrence": self.first_occurrence,
            "last_occurrence": self.last_occurrence,
            "occurrence_count": self.occurrence_count,
            "source_address": self.source_address,
            "pgn": self.pgn,
            "dgn": self.dgn,
            "description": self.description,
            "possible_causes": self.possible_causes,
            "recommended_actions": self.recommended_actions,
            "active": self.active,
            "intermittent": self.intermittent,
            "resolved": self.resolved,
            "acknowledged": self.acknowledged,
            "metadata": self.metadata,
        }


@dataclass
class FaultCorrelation:
    """Correlated fault analysis across multiple systems."""

    primary_dtc: DiagnosticTroubleCode
    related_dtcs: list[DiagnosticTroubleCode]
    correlation_confidence: float  # 0.0 to 1.0
    correlation_type: str  # "causal", "symptomatic", "temporal"

    # Analysis results
    root_cause_hypothesis: str = ""
    system_impact_analysis: dict[SystemType, str] = field(default_factory=dict)
    recommended_investigation: list[str] = field(default_factory=list)

    # Timing analysis
    time_window_seconds: float = 60.0  # Correlation time window
    sequence_analysis: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "primary_dtc": self.primary_dtc.to_dict(),
            "related_dtcs": [dtc.to_dict() for dtc in self.related_dtcs],
            "correlation_confidence": self.correlation_confidence,
            "correlation_type": self.correlation_type,
            "root_cause_hypothesis": self.root_cause_hypothesis,
            "system_impact_analysis": {k.value: v for k, v in self.system_impact_analysis.items()},
            "recommended_investigation": self.recommended_investigation,
            "time_window_seconds": self.time_window_seconds,
            "sequence_analysis": self.sequence_analysis,
        }


@dataclass
class MaintenancePrediction:
    """Predictive maintenance recommendation."""

    system_type: SystemType
    component_name: str
    predicted_failure_date: float | None = None
    confidence: float = 0.0  # 0.0 to 1.0
    urgency: MaintenanceUrgency = MaintenanceUrgency.MONITOR

    # Supporting data
    trend_analysis: dict[str, Any] = field(default_factory=dict)
    historical_patterns: list[str] = field(default_factory=list)
    performance_degradation: dict[str, float] = field(default_factory=dict)

    # Recommendations
    recommended_actions: list[str] = field(default_factory=list)
    estimated_cost: float | None = None
    estimated_downtime_hours: float | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "system_type": self.system_type.value,
            "component_name": self.component_name,
            "predicted_failure_date": self.predicted_failure_date,
            "confidence": self.confidence,
            "urgency": self.urgency.value,
            "trend_analysis": self.trend_analysis,
            "historical_patterns": self.historical_patterns,
            "performance_degradation": self.performance_degradation,
            "recommended_actions": self.recommended_actions,
            "estimated_cost": self.estimated_cost,
            "estimated_downtime_hours": self.estimated_downtime_hours,
        }


@dataclass
class ServiceRecommendation:
    """Service recommendation based on diagnostic analysis."""

    title: str
    description: str
    urgency: MaintenanceUrgency

    # Scope
    affected_systems: list[SystemType] = field(default_factory=list)
    related_dtcs: list[DiagnosticTroubleCode] = field(default_factory=list)

    # Service details
    estimated_duration_hours: float | None = None
    estimated_cost: float | None = None
    required_parts: list[str] = field(default_factory=list)
    required_tools: list[str] = field(default_factory=list)
    skill_level_required: str = "basic"  # basic, intermediate, advanced, professional

    # Scheduling
    can_defer: bool = True
    max_defer_days: int | None = None
    seasonal_considerations: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "title": self.title,
            "description": self.description,
            "urgency": self.urgency.value,
            "affected_systems": [s.value for s in self.affected_systems],
            "related_dtcs": [dtc.to_dict() for dtc in self.related_dtcs],
            "estimated_duration_hours": self.estimated_duration_hours,
            "estimated_cost": self.estimated_cost,
            "required_parts": self.required_parts,
            "required_tools": self.required_tools,
            "skill_level_required": self.skill_level_required,
            "can_defer": self.can_defer,
            "max_defer_days": self.max_defer_days,
            "seasonal_considerations": self.seasonal_considerations,
        }


@dataclass
class SystemHealthStatus:
    """Overall system health status."""

    system_type: SystemType
    health_score: float = 1.0  # 0.0 to 1.0 (1.0 = perfect health)
    status: str = "excellent"  # "excellent", "good", "fair", "poor", "critical"

    # Component status
    active_dtcs: list[DiagnosticTroubleCode] = field(default_factory=list)
    maintenance_predictions: list[MaintenancePrediction] = field(default_factory=list)
    service_recommendations: list[ServiceRecommendation] = field(default_factory=list)

    # Performance metrics
    uptime_percentage: float = 100.0
    performance_trend: str = "stable"  # "improving", "stable", "degrading"
    last_assessment: float = field(default_factory=time.time)

    # Historical data
    health_history: list[tuple[float, float]] = field(
        default_factory=list
    )  # (timestamp, health_score)

    def update_health_score(self, new_score: float) -> None:
        """Update health score and maintain history."""
        self.health_history.append((time.time(), self.health_score))
        self.health_score = new_score
        self.last_assessment = time.time()

        # Determine status based on score
        if new_score >= 0.9:
            self.status = "excellent"
        elif new_score >= 0.75:
            self.status = "good"
        elif new_score >= 0.5:
            self.status = "fair"
        elif new_score >= 0.25:
            self.status = "poor"
        else:
            self.status = "critical"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "system_type": self.system_type.value,
            "health_score": self.health_score,
            "status": self.status,
            "active_dtcs": [dtc.to_dict() for dtc in self.active_dtcs],
            "maintenance_predictions": [pred.to_dict() for pred in self.maintenance_predictions],
            "service_recommendations": [rec.to_dict() for rec in self.service_recommendations],
            "uptime_percentage": self.uptime_percentage,
            "performance_trend": self.performance_trend,
            "last_assessment": self.last_assessment,
            "health_history": self.health_history,
        }
