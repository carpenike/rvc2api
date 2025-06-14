"""
Notification Analytics Service

This service provides comprehensive analytics and metrics collection for the
notification system, including real-time metrics, aggregation, and reporting.
"""

import asyncio
import csv
import json
import logging
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.notification import (
    NotificationChannel,
    NotificationPayload,
    NotificationStatus,
    NotificationType,
)
from backend.models.notification_analytics import (
    AggregationPeriod,
    ChannelMetrics,
    MetricType,
    NotificationDeliveryLog,
    NotificationErrorAnalysis,
    NotificationMetric,
    NotificationMetricAggregate,
    NotificationQueueHealth,
)
from backend.models.notification_analytics import (
    NotificationReport as NotificationReportModel,
)
from backend.services.database_manager import DatabaseManager


class NotificationAnalyticsService:
    """
    Service for collecting, aggregating, and analyzing notification metrics.

    Provides real-time metric collection, historical aggregation, error analysis,
    and comprehensive reporting capabilities.
    """

    def __init__(self, database_manager: DatabaseManager):
        """
        Initialize the analytics service.

        Args:
            database_manager: Database manager for persistence
        """
        self.db_manager = database_manager
        self.logger = logging.getLogger(f"{__name__}.NotificationAnalyticsService")

        # In-memory buffers for batch processing
        self._metric_buffer: list[NotificationDeliveryLog] = []
        self._buffer_lock = asyncio.Lock()
        self._buffer_size_limit = 100
        self._buffer_flush_interval = 30.0  # seconds

        # Background tasks
        self._aggregation_task: asyncio.Task | None = None
        self._flush_task: asyncio.Task | None = None
        self._health_monitor_task: asyncio.Task | None = None
        self._running = False

        # Metric calculation cache
        self._metric_cache: dict[str, Any] = {}
        self._cache_ttl = 300  # 5 minutes

    async def start(self) -> None:
        """Start background analytics tasks."""
        if self._running:
            return

        self._running = True

        # Start background tasks
        self._flush_task = asyncio.create_task(self._flush_buffer_loop())
        self._aggregation_task = asyncio.create_task(self._aggregation_loop())
        self._health_monitor_task = asyncio.create_task(self._health_monitor_loop())

        self.logger.info("NotificationAnalyticsService started")

    async def stop(self) -> None:
        """Stop background analytics tasks."""
        if not self._running:
            return

        self._running = False

        # Cancel background tasks
        for task in [self._flush_task, self._aggregation_task, self._health_monitor_task]:
            if task and not task.done():
                task.cancel()

        # Flush remaining metrics
        await self._flush_buffer()

        self.logger.info("NotificationAnalyticsService stopped")

    async def track_delivery(
        self,
        notification: NotificationPayload,
        channel: NotificationChannel,
        status: NotificationStatus,
        delivery_time_ms: int | None = None,
        error_message: str | None = None,
        error_code: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Track a notification delivery attempt.

        Args:
            notification: The notification that was delivered
            channel: Channel used for delivery
            status: Delivery status
            delivery_time_ms: Time taken for delivery in milliseconds
            error_message: Error message if failed
            error_code: Structured error code if failed
            metadata: Additional metadata
        """
        log_entry = NotificationDeliveryLog(
            notification_id=notification.id,
            channel=channel.value,
            notification_type=notification.level.value,
            status=status.value,
            recipient=notification.recipient,
            delivered_at=datetime.now(UTC) if status == NotificationStatus.DELIVERED else None,
            delivery_time_ms=delivery_time_ms,
            retry_count=notification.retry_count,
            error_message=error_message,
            error_code=error_code,
            metadata=metadata or {},
        )

        async with self._buffer_lock:
            self._metric_buffer.append(log_entry)

            # Flush if buffer is full
            if len(self._metric_buffer) >= self._buffer_size_limit:
                await self._flush_buffer()

    async def track_engagement(
        self,
        notification_id: str,
        action: str,  # opened, clicked, dismissed
        timestamp: datetime | None = None,
    ) -> None:
        """
        Track user engagement with a notification.

        Args:
            notification_id: ID of the notification
            action: Engagement action (opened, clicked, dismissed)
            timestamp: When the action occurred
        """
        if timestamp is None:
            timestamp = datetime.now(UTC)

        async with self.db_manager.get_session() as session:
            # Update the delivery log with engagement data
            stmt = select(NotificationDeliveryLog).where(
                NotificationDeliveryLog.notification_id == notification_id
            )
            result = await session.execute(stmt)
            log_entry = result.scalar_one_or_none()

            if log_entry:
                if action == "opened":
                    log_entry.opened_at = timestamp
                elif action == "clicked":
                    log_entry.clicked_at = timestamp
                elif action == "dismissed":
                    log_entry.dismissed_at = timestamp

                await session.commit()

    async def get_channel_metrics(
        self,
        channel: NotificationChannel | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[ChannelMetrics]:
        """
        Get metrics for notification channels.

        Args:
            channel: Optional specific channel to filter
            start_date: Start of period
            end_date: End of period

        Returns:
            List of channel metrics
        """
        if end_date is None:
            end_date = datetime.now(UTC)
        if start_date is None:
            start_date = end_date - timedelta(days=7)

        async with self.db_manager.get_session() as session:
            # Build base query
            query = select(
                NotificationDeliveryLog.channel,
                func.count().label("total"),
                func.sum(
                    func.cast(
                        NotificationDeliveryLog.status == NotificationStatus.DELIVERED.value,
                        func.Integer
                    )
                ).label("delivered"),
                func.sum(
                    func.cast(
                        NotificationDeliveryLog.status == NotificationStatus.FAILED.value,
                        func.Integer
                    )
                ).label("failed"),
                func.sum(NotificationDeliveryLog.retry_count).label("retries"),
                func.avg(NotificationDeliveryLog.delivery_time_ms).label("avg_delivery_time"),
            ).where(
                and_(
                    NotificationDeliveryLog.created_at >= start_date,
                    NotificationDeliveryLog.created_at <= end_date,
                )
            )

            if channel:
                query = query.where(NotificationDeliveryLog.channel == channel.value)

            query = query.group_by(NotificationDeliveryLog.channel)

            result = await session.execute(query)
            rows = result.all()

            metrics = []
            for row in rows:
                # Get last success/failure times
                last_success_stmt = select(
                    func.max(NotificationDeliveryLog.delivered_at)
                ).where(
                    and_(
                        NotificationDeliveryLog.channel == row.channel,
                        NotificationDeliveryLog.status == NotificationStatus.DELIVERED.value,
                    )
                )
                last_success = await session.scalar(last_success_stmt)

                last_failure_stmt = select(
                    func.max(NotificationDeliveryLog.created_at)
                ).where(
                    and_(
                        NotificationDeliveryLog.channel == row.channel,
                        NotificationDeliveryLog.status == NotificationStatus.FAILED.value,
                    )
                )
                last_failure = await session.scalar(last_failure_stmt)

                # Get error breakdown
                error_stmt = select(
                    NotificationDeliveryLog.error_code,
                    func.count().label("count")
                ).where(
                    and_(
                        NotificationDeliveryLog.channel == row.channel,
                        NotificationDeliveryLog.error_code.isnot(None),
                        NotificationDeliveryLog.created_at >= start_date,
                        NotificationDeliveryLog.created_at <= end_date,
                    )
                ).group_by(NotificationDeliveryLog.error_code)

                error_result = await session.execute(error_stmt)
                error_breakdown = {err.error_code: err.count for err in error_result}

                metrics.append(
                    ChannelMetrics(
                        channel=NotificationChannel(row.channel),
                        total_sent=row.total or 0,
                        total_delivered=row.delivered or 0,
                        total_failed=row.failed or 0,
                        total_retried=row.retries or 0,
                        success_rate=(row.delivered or 0) / max(row.total, 1),
                        average_delivery_time=row.avg_delivery_time,
                        last_success=last_success,
                        last_failure=last_failure,
                        error_breakdown=error_breakdown,
                    )
                )

            return metrics

    async def get_aggregated_metrics(
        self,
        metric_type: MetricType,
        aggregation_period: AggregationPeriod,
        start_date: datetime,
        end_date: datetime | None = None,
        channel: NotificationChannel | None = None,
        notification_type: NotificationType | None = None,
    ) -> list[NotificationMetric]:
        """
        Get aggregated metrics for a specific period.

        Args:
            metric_type: Type of metric to retrieve
            aggregation_period: Aggregation period
            start_date: Start of period
            end_date: End of period
            channel: Optional channel filter
            notification_type: Optional notification type filter

        Returns:
            List of metric data points
        """
        if end_date is None:
            end_date = datetime.now(UTC)

        async with self.db_manager.get_session() as session:
            query = select(NotificationMetricAggregate).where(
                and_(
                    NotificationMetricAggregate.metric_type == metric_type.value,
                    NotificationMetricAggregate.aggregation_period == aggregation_period.value,
                    NotificationMetricAggregate.period_start >= start_date,
                    NotificationMetricAggregate.period_start <= end_date,
                )
            )

            if channel:
                query = query.where(NotificationMetricAggregate.channel == channel.value)
            if notification_type:
                query = query.where(
                    NotificationMetricAggregate.notification_type == notification_type.value
                )

            result = await session.execute(query.order_by(NotificationMetricAggregate.period_start))
            aggregates = result.scalars().all()

            return [
                NotificationMetric(
                    timestamp=agg.period_start,
                    metric_type=MetricType(agg.metric_type),
                    value=agg.value,
                    channel=NotificationChannel(agg.channel) if agg.channel else None,
                    notification_type=NotificationType(agg.notification_type)
                    if agg.notification_type
                    else None,
                    metadata=agg.metadata or {},
                )
                for agg in aggregates
            ]

    async def analyze_errors(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        min_occurrences: int = 5,
    ) -> list[NotificationErrorAnalysis]:
        """
        Analyze notification delivery errors.

        Args:
            start_date: Start of analysis period
            end_date: End of analysis period
            min_occurrences: Minimum occurrences to include

        Returns:
            List of error analysis records
        """
        if end_date is None:
            end_date = datetime.now(UTC)
        if start_date is None:
            start_date = end_date - timedelta(days=7)

        async with self.db_manager.get_session() as session:
            # Get error patterns
            query = select(
                NotificationDeliveryLog.error_code,
                NotificationDeliveryLog.error_message,
                NotificationDeliveryLog.channel,
                func.count().label("count"),
                func.min(NotificationDeliveryLog.created_at).label("first_seen"),
                func.max(NotificationDeliveryLog.created_at).label("last_seen"),
                func.count(func.distinct(NotificationDeliveryLog.recipient)).label("affected_recipients"),
            ).where(
                and_(
                    NotificationDeliveryLog.error_code.isnot(None),
                    NotificationDeliveryLog.created_at >= start_date,
                    NotificationDeliveryLog.created_at <= end_date,
                )
            ).group_by(
                NotificationDeliveryLog.error_code,
                NotificationDeliveryLog.error_message,
                NotificationDeliveryLog.channel,
            ).having(
                func.count() >= min_occurrences
            )

            result = await session.execute(query)
            error_patterns = result.all()

            # Analyze each error pattern
            analyses = []
            for pattern in error_patterns:
                # Calculate retry success rate
                retry_success_stmt = select(
                    func.count()
                ).select_from(
                    NotificationDeliveryLog
                ).where(
                    and_(
                        NotificationDeliveryLog.error_code == pattern.error_code,
                        NotificationDeliveryLog.channel == pattern.channel,
                        NotificationDeliveryLog.retry_count > 0,
                        NotificationDeliveryLog.status == NotificationStatus.DELIVERED.value,
                    )
                )
                retry_successes = await session.scalar(retry_success_stmt) or 0
                retry_success_rate = retry_successes / max(pattern.count, 1)

                # Determine recommended action based on error type
                recommended_action = self._get_error_recommendation(
                    pattern.error_code,
                    pattern.error_message,
                    retry_success_rate
                )

                analysis = NotificationErrorAnalysis(
                    error_code=pattern.error_code,
                    error_message=pattern.error_message or "Unknown error",
                    channel=pattern.channel,
                    occurrence_count=pattern.count,
                    first_seen=pattern.first_seen,
                    last_seen=pattern.last_seen,
                    affected_recipients=pattern.affected_recipients,
                    retry_success_rate=retry_success_rate,
                    recommended_action=recommended_action,
                    is_resolved=pattern.last_seen < (datetime.now(UTC) - timedelta(hours=24)),
                )

                analyses.append(analysis)

            # Save analyses to database
            session.add_all(analyses)
            await session.commit()

            return analyses

    async def generate_report(
        self,
        report_type: str,
        start_date: datetime,
        end_date: datetime,
        format: str = "json",
        parameters: dict[str, Any] | None = None,
        generated_by: str | None = None,
    ) -> NotificationReportModel:
        """
        Generate a comprehensive notification report.

        Args:
            report_type: Type of report to generate
            start_date: Report period start
            end_date: Report period end
            format: Output format (json, csv, pdf)
            parameters: Additional report parameters
            generated_by: User who generated the report

        Returns:
            Generated report model
        """
        report_id = str(uuid4())
        report_name = f"{report_type}_report_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}"

        # Collect report data
        report_data = await self._collect_report_data(
            report_type, start_date, end_date, parameters
        )

        # Generate report file
        file_path, file_size = await self._generate_report_file(
            report_id, report_data, format
        )

        # Create report record
        report_model = NotificationReportModel(
            report_id=report_id,
            report_type=report_type,
            report_name=report_name,
            start_date=start_date,
            end_date=end_date,
            generated_by=generated_by,
            format=format,
            file_path=file_path,
            file_size_bytes=file_size,
            summary_data=report_data["summary"],
            parameters=parameters,
            is_scheduled=False,
        )

        async with self.db_manager.get_session() as session:
            session.add(report_model)
            await session.commit()

        return report_model

    async def get_queue_health(self) -> NotificationQueueHealth:
        """
        Get current notification queue health metrics.

        Returns:
            Current queue health status
        """
        # This would integrate with the actual queue service
        # For now, return a sample implementation
        async with self.db_manager.get_session() as session:
            # Get queue statistics from last hour
            one_hour_ago = datetime.now(UTC) - timedelta(hours=1)

            # Count pending notifications
            pending_count_stmt = select(func.count()).select_from(
                NotificationDeliveryLog
            ).where(
                NotificationDeliveryLog.status == NotificationStatus.PENDING.value
            )
            pending_count = await session.scalar(pending_count_stmt) or 0

            # Calculate processing rate
            processed_stmt = select(func.count()).select_from(
                NotificationDeliveryLog
            ).where(
                and_(
                    NotificationDeliveryLog.created_at >= one_hour_ago,
                    NotificationDeliveryLog.status.in_(
                        [NotificationStatus.DELIVERED.value, NotificationStatus.FAILED.value]
                    ),
                )
            )
            processed_count = await session.scalar(processed_stmt) or 0
            processing_rate = processed_count / 3600.0  # per second

            # Calculate success rate
            success_stmt = select(func.count()).select_from(
                NotificationDeliveryLog
            ).where(
                and_(
                    NotificationDeliveryLog.created_at >= one_hour_ago,
                    NotificationDeliveryLog.status == NotificationStatus.DELIVERED.value,
                )
            )
            success_count = await session.scalar(success_stmt) or 0
            success_rate = success_count / max(processed_count, 1)

            # Calculate average times
            avg_wait_stmt = select(
                func.avg(
                    func.extract(
                        "epoch",
                        NotificationDeliveryLog.delivered_at - NotificationDeliveryLog.created_at
                    )
                )
            ).where(
                and_(
                    NotificationDeliveryLog.created_at >= one_hour_ago,
                    NotificationDeliveryLog.delivered_at.isnot(None),
                )
            )
            avg_wait_time = await session.scalar(avg_wait_stmt) or 0.0

            avg_processing_stmt = select(
                func.avg(NotificationDeliveryLog.delivery_time_ms)
            ).where(
                and_(
                    NotificationDeliveryLog.created_at >= one_hour_ago,
                    NotificationDeliveryLog.delivery_time_ms.isnot(None),
                )
            )
            avg_processing_time = (await session.scalar(avg_processing_stmt) or 0.0) / 1000.0

            # Calculate health score
            health_score = self._calculate_health_score(
                pending_count,
                processing_rate,
                success_rate,
                avg_wait_time,
            )

            return NotificationQueueHealth(
                timestamp=datetime.now(UTC),
                queue_depth=pending_count,
                processing_rate=processing_rate,
                success_rate=success_rate,
                average_wait_time=avg_wait_time,
                average_processing_time=avg_processing_time,
                dlq_size=0,  # Would come from actual queue
                active_workers=1,  # Would come from dispatcher
                memory_usage_mb=None,
                cpu_usage_percent=None,
                health_score=health_score,
            )

    # Background task methods

    async def _flush_buffer_loop(self) -> None:
        """Background loop to flush metric buffer periodically."""
        while self._running:
            try:
                await asyncio.sleep(self._buffer_flush_interval)
                await self._flush_buffer()
            except Exception as e:
                self.logger.error(f"Buffer flush error: {e}")

    async def _flush_buffer(self) -> None:
        """Flush metric buffer to database."""
        async with self._buffer_lock:
            if not self._metric_buffer:
                return

            buffer_copy = self._metric_buffer.copy()
            self._metric_buffer.clear()

        try:
            async with self.db_manager.get_session() as session:
                session.add_all(buffer_copy)
                await session.commit()

            self.logger.debug(f"Flushed {len(buffer_copy)} delivery logs to database")
        except Exception as e:
            self.logger.error(f"Failed to flush metric buffer: {e}")
            # Re-add to buffer on failure
            async with self._buffer_lock:
                self._metric_buffer.extend(buffer_copy)

    async def _aggregation_loop(self) -> None:
        """Background loop to perform metric aggregation."""
        while self._running:
            try:
                # Run aggregation every hour
                await asyncio.sleep(3600)
                await self._perform_aggregation()
            except Exception as e:
                self.logger.error(f"Aggregation error: {e}")

    async def _perform_aggregation(self) -> None:
        """Perform metric aggregation for different periods."""
        end_time = datetime.now(UTC)

        # Hourly aggregation for last 24 hours
        await self._aggregate_period(
            AggregationPeriod.HOURLY,
            end_time - timedelta(days=1),
            end_time,
            timedelta(hours=1)
        )

        # Daily aggregation for last 30 days
        await self._aggregate_period(
            AggregationPeriod.DAILY,
            end_time - timedelta(days=30),
            end_time,
            timedelta(days=1)
        )

        # Weekly aggregation for last 12 weeks
        await self._aggregate_period(
            AggregationPeriod.WEEKLY,
            end_time - timedelta(weeks=12),
            end_time,
            timedelta(weeks=1)
        )

    async def _aggregate_period(
        self,
        period: AggregationPeriod,
        start_date: datetime,
        end_date: datetime,
        interval: timedelta,
    ) -> None:
        """Aggregate metrics for a specific period."""
        async with self.db_manager.get_session() as session:
            current = start_date

            while current < end_date:
                period_end = min(current + interval, end_date)

                # Aggregate each metric type
                for metric_type in MetricType:
                    await self._aggregate_metric(
                        session,
                        metric_type,
                        period,
                        current,
                        period_end,
                    )

                current = period_end

            await session.commit()

    async def _aggregate_metric(
        self,
        session: AsyncSession,
        metric_type: MetricType,
        period: AggregationPeriod,
        start: datetime,
        end: datetime,
    ) -> None:
        """Aggregate a specific metric for a period."""
        # Check if aggregation already exists
        exists_stmt = select(func.count()).select_from(
            NotificationMetricAggregate
        ).where(
            and_(
                NotificationMetricAggregate.metric_type == metric_type.value,
                NotificationMetricAggregate.aggregation_period == period.value,
                NotificationMetricAggregate.period_start == start,
            )
        )

        exists_count = await session.scalar(exists_stmt)
        if exists_count and exists_count > 0:
            return

        # Calculate aggregation based on metric type
        if metric_type == MetricType.DELIVERY_COUNT:
            value_stmt = select(func.count()).select_from(
                NotificationDeliveryLog
            ).where(
                and_(
                    NotificationDeliveryLog.created_at >= start,
                    NotificationDeliveryLog.created_at < end,
                )
            )
            value = await session.scalar(value_stmt) or 0

        elif metric_type == MetricType.SUCCESS_RATE:
            total_stmt = select(func.count()).select_from(
                NotificationDeliveryLog
            ).where(
                and_(
                    NotificationDeliveryLog.created_at >= start,
                    NotificationDeliveryLog.created_at < end,
                )
            )
            total = await session.scalar(total_stmt) or 0

            success_stmt = select(func.count()).select_from(
                NotificationDeliveryLog
            ).where(
                and_(
                    NotificationDeliveryLog.created_at >= start,
                    NotificationDeliveryLog.created_at < end,
                    NotificationDeliveryLog.status == NotificationStatus.DELIVERED.value,
                )
            )
            success = await session.scalar(success_stmt) or 0

            value = success / max(total, 1)

        elif metric_type == MetricType.AVERAGE_DELIVERY_TIME:
            avg_stmt = select(
                func.avg(NotificationDeliveryLog.delivery_time_ms)
            ).where(
                and_(
                    NotificationDeliveryLog.created_at >= start,
                    NotificationDeliveryLog.created_at < end,
                    NotificationDeliveryLog.delivery_time_ms.isnot(None),
                )
            )
            value = await session.scalar(avg_stmt) or 0.0

        else:
            # Add more metric type calculations as needed
            value = 0.0

        # Create aggregation record
        aggregate = NotificationMetricAggregate(
            metric_type=metric_type.value,
            aggregation_period=period.value,
            period_start=start,
            period_end=end,
            value=value,
            count=1,  # Would be calculated properly
        )

        session.add(aggregate)

    async def _health_monitor_loop(self) -> None:
        """Background loop to monitor queue health."""
        while self._running:
            try:
                # Monitor health every 5 minutes
                await asyncio.sleep(300)

                health = await self.get_queue_health()

                async with self.db_manager.get_session() as session:
                    session.add(health)
                    await session.commit()

            except Exception as e:
                self.logger.error(f"Health monitoring error: {e}")

    # Helper methods

    def _get_error_recommendation(
        self,
        error_code: str,
        error_message: str,
        retry_success_rate: float,
    ) -> str:
        """Get recommended action for an error pattern."""
        # Common error patterns and recommendations
        if "timeout" in error_message.lower():
            return "Consider increasing timeout values or checking network connectivity"
        if "authentication" in error_message.lower():
            return "Verify API credentials and authentication configuration"
        if "rate limit" in error_message.lower():
            return "Implement rate limiting or request throttling"
        if retry_success_rate > 0.7:
            return "Transient error - retries are generally successful"
        if retry_success_rate < 0.1:
            return "Persistent error - investigate root cause and consider disabling retries"
        return "Monitor error frequency and investigate if it increases"

    def _calculate_health_score(
        self,
        queue_depth: int,
        processing_rate: float,
        success_rate: float,
        avg_wait_time: float,
    ) -> float:
        """Calculate overall queue health score."""
        score = 1.0

        # Penalize high queue depth
        if queue_depth > 1000:
            score *= 0.8
        elif queue_depth > 5000:
            score *= 0.5

        # Penalize low processing rate
        if processing_rate < 1.0:
            score *= 0.9
        elif processing_rate < 0.1:
            score *= 0.7

        # Penalize low success rate
        score *= success_rate

        # Penalize high wait times
        if avg_wait_time > 300:  # 5 minutes
            score *= 0.9
        elif avg_wait_time > 600:  # 10 minutes
            score *= 0.7

        return max(0.0, min(1.0, score))

    async def _collect_report_data(
        self,
        report_type: str,
        start_date: datetime,
        end_date: datetime,
        parameters: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Collect data for report generation."""
        # Get channel metrics
        channel_metrics = await self.get_channel_metrics(
            start_date=start_date,
            end_date=end_date
        )

        # Get hourly distribution
        hourly_distribution = await self._get_hourly_distribution(
            start_date, end_date
        )

        # Get type distribution
        type_distribution = await self._get_type_distribution(
            start_date, end_date
        )

        # Get top errors
        top_errors = await self._get_top_errors(
            start_date, end_date
        )

        # Calculate summary
        total_notifications = sum(cm.total_sent for cm in channel_metrics)
        successful_deliveries = sum(cm.total_delivered for cm in channel_metrics)
        failed_deliveries = sum(cm.total_failed for cm in channel_metrics)
        retry_attempts = sum(cm.total_retried for cm in channel_metrics)

        return {
            "summary": {
                "total_notifications": total_notifications,
                "successful_deliveries": successful_deliveries,
                "failed_deliveries": failed_deliveries,
                "retry_attempts": retry_attempts,
                "overall_success_rate": successful_deliveries / max(total_notifications, 1),
            },
            "channel_metrics": [
                {
                    "channel": cm.channel.value,
                    "total_sent": cm.total_sent,
                    "success_rate": cm.success_rate,
                    "avg_delivery_time": cm.average_delivery_time,
                }
                for cm in channel_metrics
            ],
            "hourly_distribution": hourly_distribution,
            "type_distribution": type_distribution,
            "top_errors": top_errors,
        }

    async def _get_hourly_distribution(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> dict[int, int]:
        """Get hourly distribution of notifications."""
        async with self.db_manager.get_session() as session:
            stmt = select(
                func.extract("hour", NotificationDeliveryLog.created_at).label("hour"),
                func.count().label("count")
            ).where(
                and_(
                    NotificationDeliveryLog.created_at >= start_date,
                    NotificationDeliveryLog.created_at <= end_date,
                )
            ).group_by("hour")

            result = await session.execute(stmt)
            return {int(row.hour): int(row.count) for row in result}

    async def _get_type_distribution(
        self,
        start_date: datetime,
        end_date: datetime,
    ) -> dict[str, int]:
        """Get distribution by notification type."""
        async with self.db_manager.get_session() as session:
            stmt = select(
                NotificationDeliveryLog.notification_type,
                func.count().label("count")
            ).where(
                and_(
                    NotificationDeliveryLog.created_at >= start_date,
                    NotificationDeliveryLog.created_at <= end_date,
                )
            ).group_by(NotificationDeliveryLog.notification_type)

            result = await session.execute(stmt)
            return {str(row.notification_type): int(row.count) for row in result}

    async def _get_top_errors(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: int = 10,
    ) -> list[tuple[str, int]]:
        """Get top error messages."""
        async with self.db_manager.get_session() as session:
            stmt = select(
                NotificationDeliveryLog.error_message,
                func.count().label("count")
            ).where(
                and_(
                    NotificationDeliveryLog.created_at >= start_date,
                    NotificationDeliveryLog.created_at <= end_date,
                    NotificationDeliveryLog.error_message.isnot(None),
                )
            ).group_by(
                NotificationDeliveryLog.error_message
            ).order_by(
                func.count().desc()
            ).limit(limit)

            result = await session.execute(stmt)
            return [(str(row.error_message), int(row.count)) for row in result]

    async def _generate_report_file(
        self,
        report_id: str,
        data: dict[str, Any],
        format: str,
    ) -> tuple[str, int]:
        """Generate report file in specified format."""
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)

        if format == "json":
            file_path = reports_dir / f"{report_id}.json"
            content = json.dumps(data, indent=2, default=str)
            file_path.write_text(content)

        elif format == "csv":
            file_path = reports_dir / f"{report_id}.csv"

            # Convert to CSV format
            with open(file_path, "w", newline="") as f:
                writer = csv.writer(f)

                # Write summary
                writer.writerow(["Summary"])
                for key, value in data["summary"].items():
                    writer.writerow([key, value])

                writer.writerow([])

                # Write channel metrics
                writer.writerow(["Channel Metrics"])
                writer.writerow(["Channel", "Total Sent", "Success Rate", "Avg Delivery Time"])
                for cm in data["channel_metrics"]:
                    writer.writerow([
                        cm["channel"],
                        cm["total_sent"],
                        cm["success_rate"],
                        cm["avg_delivery_time"],
                    ])

        else:
            # PDF generation would require additional libraries
            raise ValueError(f"Unsupported format: {format}")

        file_size = file_path.stat().st_size
        return str(file_path), file_size
