"""
Analytics Storage Service

Provides mandatory SQLite persistence for analytics data using the database manager.
Simplified from dual-mode architecture to use only database storage.
"""

import logging
import time
from typing import Any

from sqlalchemy import delete, desc, select
from sqlalchemy.dialects.sqlite import insert

from backend.core.services import get_core_services
from backend.integrations.analytics_dashboard.config import AnalyticsDashboardSettings
from backend.models.analytics import (
    AnalyticsInsight,
    AnalyticsMetric,
    AnalyticsPattern,
    PatternAnalysis,
    SystemInsight,
    TrendPoint,
)

logger = logging.getLogger(__name__)


class AnalyticsStorageService:
    """
    Analytics storage service with mandatory SQLite persistence.

    Uses the database manager for all analytics data operations.
    No in-memory fallback - persistence is mandatory.
    """

    def __init__(self) -> None:
        """Initialize storage service with mandatory persistence."""
        self.settings = AnalyticsDashboardSettings()
        core_services = get_core_services()
        self._db_manager = core_services.database_manager

        logger.info("Analytics storage service initialized with mandatory SQLite persistence")

    async def record_metric(
        self, metric_name: str, value: float, metadata: dict[str, Any] | None = None
    ) -> bool:
        """
        Record metric with mandatory SQLite persistence.

        Args:
            metric_name: Name of the metric
            value: Metric value
            metadata: Optional metadata dictionary

        Returns:
            True if successful, False otherwise
        """
        try:
            # Calculate baseline deviation if we have history
            baseline_deviation = await self._calculate_baseline_deviation(metric_name, value)

            # Create metric record
            timestamp = time.time()
            trend_point = TrendPoint(
                timestamp=timestamp,
                value=value,
                baseline_deviation=baseline_deviation,
                anomaly_score=0.0,  # Will be calculated by analytics engine
            )

            metric_record = AnalyticsMetric.from_trend_point(metric_name, trend_point, metadata)

            # Store in database
            async with self._db_manager.get_session() as session:
                session.add(metric_record)
                await session.commit()

            logger.debug("Recorded metric in database: %s=%s", metric_name, value)
            return True

        except Exception as e:
            logger.exception("Error recording metric: %s", e)
            return False

    async def get_metrics_trend(self, metric_name: str, hours: int = 24) -> list[TrendPoint]:
        """
        Get metric trend data from SQLite database.

        Args:
            metric_name: Name of the metric
            hours: Number of hours of historical data to retrieve

        Returns:
            List of TrendPoint objects sorted by timestamp
        """
        try:
            cutoff_time = time.time() - (hours * 3600)

            async with self._db_manager.get_session() as session:
                result = await session.execute(
                    select(AnalyticsMetric)
                    .where(
                        AnalyticsMetric.metric_name == metric_name,
                        AnalyticsMetric.timestamp >= cutoff_time,
                    )
                    .order_by(AnalyticsMetric.timestamp.asc())
                )

                metrics = result.scalars().all()
                return [metric.to_trend_point() for metric in metrics]

        except Exception as e:
            logger.exception("Error getting metrics trend: %s", e)
            return []

    async def store_insight(self, insight: SystemInsight) -> None:
        """
        Store insight with mandatory SQLite persistence.

        Args:
            insight: SystemInsight object to store
        """
        try:
            insight_record = AnalyticsInsight.from_system_insight(insight)

            async with self._db_manager.get_session() as session:
                # Use upsert to handle duplicate insight_ids
                stmt = insert(AnalyticsInsight).values({
                    "insight_id": insight_record.insight_id,
                    "category": insight_record.category,
                    "title": insight_record.title,
                    "description": insight_record.description,
                    "severity": insight_record.severity,
                    "confidence": insight_record.confidence,
                    "impact_score": insight_record.impact_score,
                    "recommendations": insight_record.recommendations,
                    "supporting_data": insight_record.supporting_data,
                    "insight_created_at": insight_record.insight_created_at,
                    "expires_at": insight_record.expires_at,
                })
                stmt = stmt.on_conflict_do_update(
                    index_elements=["insight_id"],
                    set_={
                        "category": stmt.excluded.category,
                        "title": stmt.excluded.title,
                        "description": stmt.excluded.description,
                        "severity": stmt.excluded.severity,
                        "confidence": stmt.excluded.confidence,
                        "impact_score": stmt.excluded.impact_score,
                        "recommendations": stmt.excluded.recommendations,
                        "supporting_data": stmt.excluded.supporting_data,
                        "insight_created_at": stmt.excluded.insight_created_at,
                        "expires_at": stmt.excluded.expires_at,
                    },
                )
                await session.execute(stmt)
                await session.commit()

            logger.debug("Stored insight in database: %s", insight.insight_id)

        except Exception as e:
            logger.exception("Error storing insight: %s", e)

    async def get_insights(
        self,
        categories: list[str] | None = None,
        min_severity: str = "low",
        limit: int = 50,
        max_age_hours: int = 24,
    ) -> list[SystemInsight]:
        """
        Get insights from SQLite database with filtering.

        Args:
            categories: Optional list of categories to filter by
            min_severity: Minimum severity level
            limit: Maximum number of insights to return
            max_age_hours: Maximum age in hours

        Returns:
            List of SystemInsight objects sorted by severity and impact
        """
        try:
            cutoff_time = time.time() - (max_age_hours * 3600)
            severity_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
            min_severity_level = severity_order.get(min_severity, 0)

            async with self._db_manager.get_session() as session:
                query = select(AnalyticsInsight).where(
                    AnalyticsInsight.insight_created_at >= cutoff_time
                )

                # Add category filter if specified
                if categories:
                    query = query.where(AnalyticsInsight.category.in_(categories))

                # Add severity filter
                severity_values = [
                    sev for sev, level in severity_order.items() if level >= min_severity_level
                ]
                query = query.where(AnalyticsInsight.severity.in_(severity_values))

                # Order by severity (critical first), then impact score, then confidence
                query = query.order_by(
                    desc(AnalyticsInsight.severity),
                    desc(AnalyticsInsight.impact_score),
                    desc(AnalyticsInsight.confidence),
                ).limit(limit)

                result = await session.execute(query)
                insights = result.scalars().all()

                return [insight.to_system_insight() for insight in insights]

        except Exception as e:
            logger.exception("Error getting insights: %s", e)
            return []

    async def store_pattern(self, pattern: PatternAnalysis) -> None:
        """
        Store pattern with mandatory SQLite persistence.

        Args:
            pattern: PatternAnalysis object to store
        """
        try:
            pattern_record = AnalyticsPattern.from_pattern_analysis(pattern)

            async with self._db_manager.get_session() as session:
                # Use upsert to handle duplicate pattern_ids
                stmt = insert(AnalyticsPattern).values(
                    pattern_id=pattern_record.pattern_id,
                    pattern_type=pattern_record.pattern_type,
                    description=pattern_record.description,
                    confidence=pattern_record.confidence,
                    frequency=pattern_record.frequency,
                    correlation_factors=pattern_record.correlation_factors,
                    prediction_window=pattern_record.prediction_window,
                    pattern_created_at=pattern_record.pattern_created_at,
                )
                stmt = stmt.on_conflict_do_update(
                    index_elements=["pattern_id"],
                    set_={
                        "pattern_type": stmt.excluded.pattern_type,
                        "description": stmt.excluded.description,
                        "confidence": stmt.excluded.confidence,
                        "frequency": stmt.excluded.frequency,
                        "correlation_factors": stmt.excluded.correlation_factors,
                        "prediction_window": stmt.excluded.prediction_window,
                        "pattern_created_at": stmt.excluded.pattern_created_at,
                    },
                )
                await session.execute(stmt)
                await session.commit()

            logger.debug("Stored pattern in database: %s", pattern.pattern_id)

        except Exception as e:
            logger.exception("Error storing pattern: %s", e)

    async def get_patterns(self, min_confidence: float = 0.5) -> list[PatternAnalysis]:
        """
        Get patterns from SQLite database.

        Args:
            min_confidence: Minimum confidence level

        Returns:
            List of PatternAnalysis objects
        """
        try:
            async with self._db_manager.get_session() as session:
                result = await session.execute(
                    select(AnalyticsPattern)
                    .where(AnalyticsPattern.confidence >= min_confidence)
                    .order_by(desc(AnalyticsPattern.confidence))
                )

                patterns = result.scalars().all()
                return [pattern.to_pattern_analysis() for pattern in patterns]

        except Exception as e:
            logger.exception("Error getting patterns: %s", e)
            return []

    async def cleanup_old_data(self) -> None:
        """Clean up old data from SQLite database."""
        try:
            cutoff_time = time.time() - (self.settings.persistence_retention_days * 24 * 3600)

            async with self._db_manager.get_session() as session:
                # Clean up old metrics
                await session.execute(
                    delete(AnalyticsMetric).where(AnalyticsMetric.timestamp < cutoff_time)
                )

                # Clean up old insights
                await session.execute(
                    delete(AnalyticsInsight).where(
                        AnalyticsInsight.insight_created_at < cutoff_time
                    )
                )

                # Clean up old patterns
                await session.execute(
                    delete(AnalyticsPattern).where(
                        AnalyticsPattern.pattern_created_at < cutoff_time
                    )
                )

                await session.commit()

            logger.debug(
                "Cleaned up analytics data older than %s days",
                self.settings.persistence_retention_days,
            )

        except Exception as e:
            logger.exception("Error during cleanup: %s", e)

    async def get_storage_stats(self) -> dict[str, Any]:
        """Get comprehensive storage statistics."""
        try:
            async with self._db_manager.get_session() as session:
                # Count metrics
                metrics_result = await session.execute(
                    select(AnalyticsMetric.metric_name).distinct()
                )
                metric_types = len(metrics_result.scalars().all())

                # Count total metric points
                total_metrics_result = await session.execute(select(AnalyticsMetric.id))
                total_metric_points = len(total_metrics_result.scalars().all())

                # Count insights
                insights_result = await session.execute(select(AnalyticsInsight.id))
                insights_count = len(insights_result.scalars().all())

                # Count patterns
                patterns_result = await session.execute(select(AnalyticsPattern.id))
                patterns_count = len(patterns_result.scalars().all())

                return {
                    "persistence_enabled": True,  # Always enabled
                    "storage_type": "mandatory_sqlite",
                    "metric_types": metric_types,
                    "total_metric_points": total_metric_points,
                    "insights_stored": insights_count,
                    "patterns_stored": patterns_count,
                    "retention_days": self.settings.persistence_retention_days,
                }

        except Exception as e:
            logger.exception("Error getting storage stats: %s", e)
            return {
                "persistence_enabled": True,
                "storage_type": "mandatory_sqlite",
                "error": str(e),
            }

    def close(self) -> None:
        """Clean up resources when service is shut down."""
        # No specific cleanup needed for SQLite storage
        # Database connections are managed by the database manager
        logger.debug("Analytics storage service closed")

    async def _calculate_baseline_deviation(self, metric_name: str, current_value: float) -> float:
        """
        Calculate baseline deviation from recent historical data.

        Args:
            metric_name: Name of the metric
            current_value: Current metric value

        Returns:
            Percentage deviation from baseline
        """
        try:
            # Get last 10 data points for baseline calculation
            async with self._db_manager.get_session() as session:
                result = await session.execute(
                    select(AnalyticsMetric.value)
                    .where(AnalyticsMetric.metric_name == metric_name)
                    .order_by(desc(AnalyticsMetric.timestamp))
                    .limit(10)
                )

                recent_values = [row[0] for row in result.fetchall()]

                if not recent_values:
                    return 0.0

                baseline = sum(recent_values) / len(recent_values)
                if baseline > 0:
                    return ((current_value - baseline) / baseline) * 100
                return 0.0

        except Exception as e:
            logger.warning("Error calculating baseline deviation: %s", e)
            return 0.0
