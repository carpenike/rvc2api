"""
Analytics Storage Service

Provides dual-mode storage for analytics data with optional persistence support.
Core functionality works entirely in-memory, with SQLite persistence as an enhancement.
"""

import json
import logging
import sqlite3
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

from backend.core.config import get_settings
from backend.integrations.analytics_dashboard.config import AnalyticsDashboardSettings
from backend.models.analytics import PatternAnalysis, SystemInsight, TrendPoint
from backend.services.feature_manager import FeatureManager

logger = logging.getLogger(__name__)


class AnalyticsMemoryStorage:
    """In-memory storage for analytics data (always available)."""

    def __init__(
        self, memory_retention_hours: int = 2, max_insights: int = 100, max_patterns: int = 50
    ) -> None:
        """Initialize memory storage with retention policy."""
        self.memory_retention_hours = memory_retention_hours
        self._max_insights = max_insights
        self._max_patterns = max_patterns
        self.metric_history: dict[str, list[TrendPoint]] = defaultdict(list)
        self.insights_cache: list[SystemInsight] = []
        self.pattern_cache: list[PatternAnalysis] = []

        logger.info(
            f"Analytics memory storage initialized with {memory_retention_hours}h retention, "
            f"{max_insights} max insights, {max_patterns} max patterns"
        )

    async def record_metric(
        self, metric_name: str, value: float, metadata: dict[str, Any] | None = None
    ) -> None:
        """Record metric in memory with automatic cleanup."""
        timestamp = time.time()

        # Calculate baseline deviation if we have history
        baseline_deviation = 0.0
        if metric_name in self.metric_history:
            recent_values = [point.value for point in self.metric_history[metric_name][-10:]]
            if recent_values:
                baseline = sum(recent_values) / len(recent_values)
                baseline_deviation = ((value - baseline) / baseline) * 100 if baseline > 0 else 0

        # Create trend point
        trend_point = TrendPoint(
            timestamp=timestamp, value=value, baseline_deviation=baseline_deviation
        )

        # Add to history
        self.metric_history[metric_name].append(trend_point)

        # Cleanup old data based on memory retention
        await self._cleanup_memory_cache(metric_name, timestamp)

        logger.debug(f"Recorded metric in memory: {metric_name}={value}")

    async def get_metrics_trend(self, metric_name: str, hours: int = 24) -> list[TrendPoint]:
        """Get metric trend from memory."""
        if metric_name not in self.metric_history:
            return []

        cutoff_time = time.time() - (hours * 3600)
        return [
            point for point in self.metric_history[metric_name] if point.timestamp >= cutoff_time
        ]

    async def store_insight(self, insight: SystemInsight) -> None:
        """Store insight in memory cache."""
        self.insights_cache.append(insight)

        # Cleanup old insights (configured limit)
        if len(self.insights_cache) > self._max_insights:
            self.insights_cache = self.insights_cache[-self._max_insights :]

        logger.debug(f"Stored insight in memory: {insight.insight_id}")

    async def get_insights(
        self,
        categories: list[str] | None = None,
        min_severity: str = "low",
        limit: int = 50,
        max_age_hours: int = 24,
    ) -> list[SystemInsight]:
        """Get insights from memory cache with filtering."""
        cutoff_time = time.time() - (max_age_hours * 3600)
        severity_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        min_severity_level = severity_order.get(min_severity, 0)

        filtered_insights = []
        for insight in self.insights_cache:
            # Check age
            if insight.created_at < cutoff_time:
                continue

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

        return filtered_insights[:limit]

    async def store_pattern(self, pattern: PatternAnalysis) -> None:
        """Store pattern in memory cache."""
        self.pattern_cache.append(pattern)

        # Cleanup old patterns (configured limit)
        if len(self.pattern_cache) > self._max_patterns:
            self.pattern_cache = self.pattern_cache[-self._max_patterns :]

        logger.debug(f"Stored pattern in memory: {pattern.pattern_id}")

    async def get_patterns(self, min_confidence: float = 0.5) -> list[PatternAnalysis]:
        """Get patterns from memory cache."""
        return [pattern for pattern in self.pattern_cache if pattern.confidence >= min_confidence]

    async def _cleanup_memory_cache(self, metric_name: str, current_time: float) -> None:
        """Clean up old metric data from memory."""
        cutoff_time = current_time - (self.memory_retention_hours * 3600)
        self.metric_history[metric_name] = [
            point for point in self.metric_history[metric_name] if point.timestamp > cutoff_time
        ]

    def get_memory_stats(self) -> dict[str, Any]:
        """Get memory storage statistics."""
        total_metrics = sum(len(history) for history in self.metric_history.values())
        return {
            "metric_types": len(self.metric_history),
            "total_metric_points": total_metrics,
            "insights_cached": len(self.insights_cache),
            "patterns_cached": len(self.pattern_cache),
            "retention_hours": self.memory_retention_hours,
        }


class AnalyticsSQLiteStorage:
    """Optional SQLite persistence for analytics data."""

    def __init__(self, db_path: str = "data/analytics.db") -> None:
        """Initialize SQLite storage."""
        self.db_path = db_path
        self._ensure_data_directory()
        self._connection: sqlite3.Connection | None = None

        # Initialize database connection and schema
        self._init_database()

        logger.info(f"Analytics SQLite storage initialized at {db_path}")

    def _ensure_data_directory(self) -> None:
        """Ensure data directory exists."""
        data_dir = Path(self.db_path).parent
        data_dir.mkdir(parents=True, exist_ok=True)

    def _init_database(self) -> None:
        """Initialize database connection and create tables."""
        try:
            self._connection = sqlite3.connect(self.db_path, check_same_thread=False)
            self._connection.row_factory = sqlite3.Row

            # Create tables
            self._create_tables()

        except Exception as e:
            logger.error(f"Failed to initialize SQLite database: {e}")
            if self._connection:
                self._connection.close()
                self._connection = None
            raise

    def _create_tables(self) -> None:
        """Create database tables and indexes."""
        if not self._connection:
            return

        cursor = self._connection.cursor()

        # Analytics metrics table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS analytics_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                metric_name TEXT NOT NULL,
                value REAL NOT NULL,
                baseline_deviation REAL DEFAULT 0.0,
                anomaly_score REAL DEFAULT 0.0,
                metadata TEXT,
                timestamp REAL NOT NULL
            )
        """
        )

        # System insights table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS analytics_insights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                insight_id TEXT UNIQUE NOT NULL,
                category TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                severity TEXT NOT NULL,
                confidence REAL NOT NULL,
                impact_score REAL NOT NULL,
                recommendations TEXT,
                supporting_data TEXT,
                created_at REAL NOT NULL,
                expires_at REAL
            )
        """
        )

        # Pattern analysis table
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS analytics_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_id TEXT UNIQUE NOT NULL,
                pattern_type TEXT NOT NULL,
                description TEXT,
                confidence REAL NOT NULL,
                frequency TEXT,
                correlation_factors TEXT,
                prediction_window INTEGER,
                created_at REAL NOT NULL
            )
        """
        )

        # Create indexes for performance
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_metrics_name_time
            ON analytics_metrics(metric_name, timestamp)
        """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_metrics_timestamp
            ON analytics_metrics(timestamp)
        """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_insights_created_at
            ON analytics_insights(created_at)
        """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_insights_severity
            ON analytics_insights(severity, created_at)
        """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_patterns_created_at
            ON analytics_patterns(created_at)
        """
        )

        self._connection.commit()
        logger.debug("SQLite tables and indexes created successfully")

    async def persist_metric(
        self,
        metric_name: str,
        timestamp: float,
        value: float,
        baseline_deviation: float = 0.0,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Persist metric to SQLite."""
        if not self._connection:
            raise RuntimeError("SQLite connection not available")

        cursor = self._connection.cursor()
        cursor.execute(
            """
            INSERT INTO analytics_metrics
            (metric_name, value, baseline_deviation, metadata, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """,
            (
                metric_name,
                value,
                baseline_deviation,
                json.dumps(metadata) if metadata else None,
                timestamp,
            ),
        )
        self._connection.commit()

    async def get_historical_metrics(self, metric_name: str, hours: int) -> list[TrendPoint]:
        """Get historical metrics from SQLite."""
        if not self._connection:
            return []

        cutoff_time = time.time() - (hours * 3600)
        cursor = self._connection.cursor()
        cursor.execute(
            """
            SELECT timestamp, value, baseline_deviation, anomaly_score
            FROM analytics_metrics
            WHERE metric_name = ? AND timestamp >= ?
            ORDER BY timestamp ASC
        """,
            (metric_name, cutoff_time),
        )

        return [
            TrendPoint(
                timestamp=row["timestamp"],
                value=row["value"],
                baseline_deviation=row["baseline_deviation"],
                anomaly_score=row["anomaly_score"],
            )
            for row in cursor.fetchall()
        ]

    async def persist_insight(self, insight: SystemInsight) -> None:
        """Persist insight to SQLite."""
        if not self._connection:
            raise RuntimeError("SQLite connection not available")

        cursor = self._connection.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO analytics_insights
            (insight_id, category, title, description, severity, confidence,
             impact_score, recommendations, supporting_data, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                insight.insight_id,
                insight.category,
                insight.title,
                insight.description,
                insight.severity,
                insight.confidence,
                insight.impact_score,
                json.dumps(insight.recommendations),
                json.dumps(insight.supporting_data),
                insight.created_at,
            ),
        )
        self._connection.commit()

    async def persist_pattern(self, pattern: PatternAnalysis) -> None:
        """Persist pattern to SQLite."""
        if not self._connection:
            raise RuntimeError("SQLite connection not available")

        cursor = self._connection.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO analytics_patterns
            (pattern_id, pattern_type, description, confidence, frequency,
             correlation_factors, prediction_window, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                pattern.pattern_id,
                pattern.pattern_type,
                pattern.description,
                pattern.confidence,
                pattern.frequency,
                json.dumps(pattern.correlation_factors),
                pattern.prediction_window,
                time.time(),
            ),
        )
        self._connection.commit()

    async def cleanup_old_data(self, retention_days: int = 30) -> None:
        """Clean up old data from SQLite."""
        if not self._connection:
            return

        cutoff_time = time.time() - (retention_days * 24 * 3600)
        cursor = self._connection.cursor()

        # Clean up old metrics
        cursor.execute(
            """
            DELETE FROM analytics_metrics WHERE timestamp < ?
        """,
            (cutoff_time,),
        )

        # Clean up old insights
        cursor.execute(
            """
            DELETE FROM analytics_insights WHERE created_at < ?
        """,
            (cutoff_time,),
        )

        # Clean up old patterns
        cursor.execute(
            """
            DELETE FROM analytics_patterns WHERE created_at < ?
        """,
            (cutoff_time,),
        )

        self._connection.commit()
        logger.debug(f"Cleaned up SQLite data older than {retention_days} days")

    def close(self) -> None:
        """Close SQLite connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.debug("SQLite connection closed")


class AnalyticsStorageService:
    """
    Unified analytics storage service with optional persistence.

    Provides dual-mode storage:
    - Memory storage (always available, core functionality)
    - SQLite persistence (optional enhancement)
    """

    def __init__(self, feature_manager: FeatureManager) -> None:
        """Initialize storage service with feature-based configuration."""
        self.feature_manager = feature_manager
        self.settings = get_settings()
        self.analytics_settings = AnalyticsDashboardSettings()

        # Core in-memory storage (always available)
        self.memory_storage = AnalyticsMemoryStorage(
            memory_retention_hours=self.analytics_settings.memory_retention_hours,
            max_insights=self.analytics_settings.max_memory_insights,
            max_patterns=self.analytics_settings.max_memory_patterns,
        )

        # Optional SQLite persistence
        self.persistence_enabled = feature_manager.is_enabled("persistence")
        self.sqlite_storage: AnalyticsSQLiteStorage | None = None

        if self.persistence_enabled:
            try:
                self.sqlite_storage = AnalyticsSQLiteStorage(self.analytics_settings.db_path)
                logger.info("Analytics persistence enabled with SQLite")
            except Exception as e:
                logger.warning(f"SQLite initialization failed, using memory-only: {e}")
                self.persistence_enabled = False
        else:
            logger.info("Analytics running in memory-only mode")

    async def record_metric(
        self, metric_name: str, value: float, metadata: dict[str, Any] | None = None
    ) -> bool:
        """
        Record metric with dual-mode storage.

        Always stores in memory, optionally persists to SQLite.
        Gracefully handles SQLite failures without affecting core functionality.
        """
        try:
            # ALWAYS store in memory for immediate access
            await self.memory_storage.record_metric(metric_name, value, metadata)

            # OPTIONALLY persist to SQLite if enabled and available
            if self.persistence_enabled and self.sqlite_storage:
                try:
                    # Get the latest trend point for persistence
                    latest_points = await self.memory_storage.get_metrics_trend(metric_name, 1)
                    if latest_points:
                        latest_point = latest_points[-1]
                        await self.sqlite_storage.persist_metric(
                            metric_name,
                            latest_point.timestamp,
                            latest_point.value,
                            latest_point.baseline_deviation,
                            metadata,
                        )
                except Exception as e:
                    logger.warning(f"Failed to persist metric to SQLite: {e}")
                    # Continue with memory-only - no functionality loss

            return True

        except Exception as e:
            logger.error(f"Error recording metric: {e}", exc_info=True)
            return False

    async def get_metrics_trend(self, metric_name: str, hours: int = 24) -> list[TrendPoint]:
        """
        Get metric trend data with intelligent fallback.

        Combines memory and historical data when persistence is available,
        falls back to memory-only when needed.
        """
        try:
            # Always start with memory data (recent, fast access)
            memory_retention_hours = self.memory_storage.memory_retention_hours
            memory_data = await self.memory_storage.get_metrics_trend(metric_name, hours)

            # If requesting more data than memory retention and persistence available
            if hours > memory_retention_hours and self.persistence_enabled and self.sqlite_storage:
                try:
                    # Get historical data from SQLite
                    historical_data = await self.sqlite_storage.get_historical_metrics(
                        metric_name, hours
                    )

                    # Merge and deduplicate (memory data takes precedence for recent)
                    return self._merge_metric_data(memory_data, historical_data)

                except Exception as e:
                    logger.warning(f"Failed to query historical data: {e}")
                    # Fall back to memory data only

            return memory_data

        except Exception as e:
            logger.error(f"Error getting metrics trend: {e}", exc_info=True)
            return []

    async def store_insight(self, insight: SystemInsight) -> None:
        """Store insight with dual-mode storage."""
        try:
            # Always store in memory
            await self.memory_storage.store_insight(insight)

            # Optionally persist to SQLite
            if self.persistence_enabled and self.sqlite_storage:
                try:
                    await self.sqlite_storage.persist_insight(insight)
                except Exception as e:
                    logger.warning(f"Failed to persist insight to SQLite: {e}")

        except Exception as e:
            logger.error(f"Error storing insight: {e}", exc_info=True)

    async def get_insights(
        self,
        categories: list[str] | None = None,
        min_severity: str = "low",
        limit: int = 50,
        max_age_hours: int = 24,
    ) -> list[SystemInsight]:
        """Get insights with memory-first approach."""
        try:
            return await self.memory_storage.get_insights(
                categories, min_severity, limit, max_age_hours
            )
        except Exception as e:
            logger.error(f"Error getting insights: {e}", exc_info=True)
            return []

    async def store_pattern(self, pattern: PatternAnalysis) -> None:
        """Store pattern with dual-mode storage."""
        try:
            # Always store in memory
            await self.memory_storage.store_pattern(pattern)

            # Optionally persist to SQLite
            if self.persistence_enabled and self.sqlite_storage:
                try:
                    await self.sqlite_storage.persist_pattern(pattern)
                except Exception as e:
                    logger.warning(f"Failed to persist pattern to SQLite: {e}")

        except Exception as e:
            logger.error(f"Error storing pattern: {e}", exc_info=True)

    async def get_patterns(self, min_confidence: float = 0.5) -> list[PatternAnalysis]:
        """Get patterns with memory-first approach."""
        try:
            return await self.memory_storage.get_patterns(min_confidence)
        except Exception as e:
            logger.error(f"Error getting patterns: {e}", exc_info=True)
            return []

    async def cleanup_old_data(self) -> None:
        """Clean up old data from both storage systems."""
        try:
            # Memory cleanup is handled automatically in record_metric

            # SQLite cleanup if enabled
            if self.persistence_enabled and self.sqlite_storage:
                await self.sqlite_storage.cleanup_old_data(
                    self.analytics_settings.persistence_retention_days
                )

        except Exception as e:
            logger.error(f"Error during cleanup: {e}", exc_info=True)

    def get_storage_stats(self) -> dict[str, Any]:
        """Get comprehensive storage statistics."""
        stats = {
            "persistence_enabled": self.persistence_enabled,
            "memory_stats": self.memory_storage.get_memory_stats(),
            "sqlite_available": self.sqlite_storage is not None,
        }

        return stats

    def close(self) -> None:
        """Clean up storage resources."""
        if self.sqlite_storage:
            self.sqlite_storage.close()

    def _merge_metric_data(
        self, memory_data: list[TrendPoint], historical_data: list[TrendPoint]
    ) -> list[TrendPoint]:
        """
        Merge memory and historical data, prioritizing memory for recent data.

        Memory data takes precedence for overlapping timestamps.
        """
        if not historical_data:
            return memory_data

        if not memory_data:
            return historical_data

        # Create lookup for memory data timestamps
        memory_timestamps = {point.timestamp for point in memory_data}

        # Add historical data that doesn't overlap with memory
        merged_data = list(memory_data)
        for historical_point in historical_data:
            if historical_point.timestamp not in memory_timestamps:
                merged_data.append(historical_point)

        # Sort by timestamp
        merged_data.sort(key=lambda x: x.timestamp)

        return merged_data
