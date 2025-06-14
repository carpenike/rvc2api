"""
Monitoring module for CoachIQ backend.

Provides comprehensive monitoring capabilities including:
- Health probe metrics and alerting
- Performance monitoring
- System resource tracking
- Safety-critical system monitoring
"""

from .health_probe_metrics import (
    health_probe_monitor,
    record_health_probe,
    get_health_monitoring_summary,
    ProbeMetric,
    ProbeStatistics,
    HealthProbeMonitor,
)

__all__ = [
    "health_probe_monitor",
    "record_health_probe",
    "get_health_monitoring_summary",
    "ProbeMetric",
    "ProbeStatistics",
    "HealthProbeMonitor",
]
