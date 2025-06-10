"""
Analytics data models and types.

Shared data classes for the analytics dashboard and storage systems.
"""

from dataclasses import dataclass, field
from typing import Any


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
