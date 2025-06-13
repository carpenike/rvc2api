"""
Notification Feature Integration

Feature integration for the unified notification system following the
established feature management patterns. This feature manages the NotificationManager
lifecycle and provides integration hooks for other features.
"""

import asyncio
import logging
from typing import Any

from backend.core.config import get_notification_settings
from backend.models.notification import NotificationChannelStatus
from backend.services.feature_base import Feature
from backend.services.notification_manager import NotificationManager

logger = logging.getLogger(__name__)


class NotificationFeature(Feature):
    """
    Notification feature providing unified multi-channel notification delivery.

    This feature manages the NotificationManager lifecycle and provides a centralized
    interface for sending notifications across all supported channels including SMTP,
    Slack, Discord, and others through Apprise integration.
    """

    def __init__(
        self,
        name: str = "notifications",
        enabled: bool = False,
        core: bool = False,
        config: dict[str, Any] | None = None,
        dependencies: list[str] | None = None,
        friendly_name: str | None = None,
    ):
        """Initialize the notification feature."""
        super().__init__(
            name=name,
            enabled=enabled,
            core=core,
            config=config,
            dependencies=dependencies,
            friendly_name=friendly_name or "Notification System",
        )

        # Get notification settings
        self.notification_settings = get_notification_settings()

        # Initialize components
        self.notification_manager: NotificationManager | None = None

        # Feature statistics
        self._stats = {
            "startup_time": 0.0,
            "notifications_sent": 0,
            "notifications_failed": 0,
            "emails_sent": 0,
            "system_notifications": 0,
            "channels_configured": 0,
            "templates_loaded": 0,
        }

        # Channel status tracking
        self._channel_status: dict[str, NotificationChannelStatus] = {}

        # Background tasks
        self._background_tasks: list[asyncio.Task] = []

    async def startup(self) -> None:
        """Initialize notification system components."""
        if not self.notification_settings.enabled:
            logger.info("Notification feature disabled")
            return

        try:
            start_time = asyncio.get_event_loop().time()

            # Initialize notification manager
            logger.info("Initializing notification manager")
            self.notification_manager = NotificationManager(self.notification_settings)

            # Get initial channel status
            enabled_channels = self.notification_settings.get_enabled_channels()
            self._stats["channels_configured"] = len(enabled_channels)

            # Initialize channel status tracking
            for channel_name, _ in enabled_channels:
                self._channel_status[channel_name] = NotificationChannelStatus(
                    channel=channel_name, enabled=True, configured=True, healthy=True
                )

            # Test notification channels (optional)
            if self.config.get("test_on_startup", False):
                await self._test_notification_channels()

            # Send startup notification
            await self._send_startup_notification()

            # Start background monitoring tasks
            await self._start_background_tasks()

            startup_time = asyncio.get_event_loop().time() - start_time
            self._stats["startup_time"] = startup_time

            logger.info(f"Notification feature started successfully ({startup_time:.2f}s)")

        except Exception as e:
            logger.error(f"Failed to start notification feature: {e}")
            # Don't fail startup for notification issues

    async def shutdown(self) -> None:
        """Shutdown notification system components."""
        try:
            # Send shutdown notification
            if self.notification_manager:
                await self.notification_manager.send_system_notification(
                    message="CoachIQ notification system shutting down",
                    level="info",
                    component="Notification System",
                )

            # Cancel background tasks
            for task in self._background_tasks:
                if not task.done():
                    task.cancel()

            if self._background_tasks:
                await asyncio.gather(*self._background_tasks, return_exceptions=True)

            self._background_tasks.clear()

            # Clean up notification manager
            self.notification_manager = None

            logger.info("Notification feature shutdown complete")

        except Exception as e:
            logger.error(f"Error during notification feature shutdown: {e}")

    @property
    def health(self) -> str:
        """Get the health status of the feature as a string."""
        if not self.notification_settings.enabled:
            return "disabled"

        if not self.notification_manager:
            return "failed"

        # Check channel health
        healthy_channels = sum(1 for status in self._channel_status.values() if status.healthy)
        total_channels = len(self._channel_status)

        if total_channels == 0:
            return "degraded"  # No channels configured

        health_ratio = healthy_channels / total_channels

        if health_ratio >= 1.0:
            return "healthy"
        if health_ratio >= 0.5:
            return "degraded"
        return "failed"

    def get_status(self) -> dict[str, Any]:
        """Get comprehensive status of the notification feature."""
        status = {
            "enabled": self.notification_settings.enabled,
            "healthy": self.health == "healthy",
            "notification_manager_initialized": self.notification_manager is not None,
            "statistics": self._stats.copy(),
            "channels": {},
            "configuration": {
                "smtp_enabled": self.notification_settings.smtp.enabled,
                "slack_enabled": self.notification_settings.slack.enabled,
                "discord_enabled": self.notification_settings.discord.enabled,
                "log_notifications": self.notification_settings.log_notifications,
                "template_path": self.notification_settings.template_path,
            },
        }

        # Add channel status
        for channel_name, channel_status in self._channel_status.items():
            status["channels"][channel_name] = {
                "enabled": channel_status.enabled,
                "healthy": channel_status.healthy,
                "configured": channel_status.configured,
                "total_sent": channel_status.total_sent,
                "total_failures": channel_status.total_failures,
                "success_rate": channel_status.success_rate,
                "last_success": channel_status.last_success.isoformat()
                if channel_status.last_success
                else None,
                "last_failure": channel_status.last_failure.isoformat()
                if channel_status.last_failure
                else None,
            }

        # Add notification manager status if available
        if self.notification_manager:
            status["notification_manager"] = self.notification_manager.get_channel_status()

        return status

    # Public API methods for other features to use

    async def send_notification(
        self,
        message: str,
        title: str | None = None,
        level: str = "info",
        tags: list[str] | None = None,
        template: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> bool:
        """
        Send notification through the notification system.

        Args:
            message: Notification message
            title: Optional notification title
            level: Notification level (info, warning, error, critical)
            tags: Optional channel tags to target
            template: Optional template name
            context: Optional template context

        Returns:
            bool: True if notification was sent successfully
        """
        if not self.notification_manager:
            logger.warning("Notification manager not initialized, cannot send notification")
            return False

        try:
            result = await self.notification_manager.send_notification(
                message=message,
                title=title,
                notify_type=level,
                tags=tags,
                template=template,
                context=context,
            )

            # Update statistics
            if result:
                self._stats["notifications_sent"] += 1
            else:
                self._stats["notifications_failed"] += 1

            return result

        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            self._stats["notifications_failed"] += 1
            return False

    async def send_email(
        self,
        to_email: str,
        subject: str,
        template: str,
        context: dict[str, Any],
        from_email: str | None = None,
    ) -> bool:
        """
        Send email notification.

        Args:
            to_email: Recipient email address
            subject: Email subject
            template: Template name
            context: Template context
            from_email: Optional override for from email

        Returns:
            bool: True if email was sent successfully
        """
        if not self.notification_manager:
            logger.warning("Notification manager not initialized, cannot send email")
            return False

        try:
            result = await self.notification_manager.send_email(
                to_email=to_email,
                subject=subject,
                template=template,
                context=context,
                from_email=from_email,
            )

            # Update statistics
            if result:
                self._stats["emails_sent"] += 1
                self._stats["notifications_sent"] += 1
            else:
                self._stats["notifications_failed"] += 1

            return result

        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {e}")
            self._stats["notifications_failed"] += 1
            return False

    async def send_magic_link_email(
        self,
        to_email: str,
        magic_link: str,
        user_name: str | None = None,
        expires_minutes: int = 15,
    ) -> bool:
        """
        Send magic link authentication email.

        Args:
            to_email: Recipient email address
            magic_link: Magic link URL
            user_name: Optional user display name
            expires_minutes: Link expiration time

        Returns:
            bool: True if email was sent successfully
        """
        if not self.notification_manager:
            logger.warning("Notification manager not initialized, cannot send magic link email")
            return False

        try:
            result = await self.notification_manager.send_magic_link_email(
                to_email=to_email,
                magic_link=magic_link,
                user_name=user_name,
                expires_minutes=expires_minutes,
            )

            # Update statistics
            if result:
                self._stats["emails_sent"] += 1
                self._stats["notifications_sent"] += 1
            else:
                self._stats["notifications_failed"] += 1

            return result

        except Exception as e:
            logger.error(f"Error sending magic link email to {to_email}: {e}")
            self._stats["notifications_failed"] += 1
            return False

    async def send_system_notification(
        self, message: str, level: str = "info", component: str | None = None
    ) -> bool:
        """
        Send system notification.

        Args:
            message: System notification message
            level: Notification level
            component: Optional component name

        Returns:
            bool: True if notification was sent successfully
        """
        if not self.notification_manager:
            logger.warning("Notification manager not initialized, cannot send system notification")
            return False

        try:
            result = await self.notification_manager.send_system_notification(
                message=message, level=level, component=component
            )

            # Update statistics
            if result:
                self._stats["system_notifications"] += 1
                self._stats["notifications_sent"] += 1
            else:
                self._stats["notifications_failed"] += 1

            return result

        except Exception as e:
            logger.error(f"Error sending system notification: {e}")
            self._stats["notifications_failed"] += 1
            return False

    async def test_channels(self) -> dict[str, bool]:
        """Test all configured notification channels."""
        if not self.notification_manager:
            return {"error": "Notification manager not initialized"}

        try:
            return await self.notification_manager.test_channels()
        except Exception as e:
            logger.error(f"Error testing notification channels: {e}")
            return {"error": str(e)}

    # Internal helper methods

    async def _send_startup_notification(self) -> None:
        """Send startup notification."""
        if not self.notification_manager:
            return

        try:
            enabled_channels = self.notification_settings.get_enabled_channels()
            channel_names = [name for name, _ in enabled_channels]

            message = (
                f"CoachIQ notification system started successfully with "
                f"{len(channel_names)} channels: {', '.join(channel_names)}"
            )

            await self.notification_manager.send_system_notification(
                message=message, level="info", component="Notification System"
            )

        except Exception as e:
            logger.warning(f"Failed to send startup notification: {e}")

    async def _test_notification_channels(self) -> None:
        """Test notification channels on startup."""
        if not self.notification_manager:
            return

        try:
            logger.info("Testing notification channels...")
            results = await self.notification_manager.test_channels()

            for channel, success in results.items():
                if channel in self._channel_status:
                    self._channel_status[channel].healthy = success
                    if not success:
                        logger.warning(f"Notification channel {channel} test failed")
                    else:
                        logger.debug(f"Notification channel {channel} test passed")

        except Exception as e:
            logger.warning(f"Error testing notification channels: {e}")

    async def _start_background_tasks(self) -> None:
        """Start background monitoring tasks."""
        try:
            # Start channel health monitoring task
            if self.config.get("enable_health_monitoring", True):
                health_task = asyncio.create_task(self._health_monitoring_loop())
                self._background_tasks.append(health_task)

        except Exception as e:
            logger.warning(f"Error starting background tasks: {e}")

    async def _health_monitoring_loop(self) -> None:
        """Background task for monitoring notification channel health."""
        while True:
            try:
                # Test channels periodically
                if self.notification_manager:
                    results = await self.notification_manager.test_channels()

                    for channel, success in results.items():
                        if channel in self._channel_status:
                            status = self._channel_status[channel]
                            status.healthy = success

                            if not success:
                                status.consecutive_failures += 1
                                logger.warning(
                                    f"Notification channel {channel} health check failed "
                                    f"({status.consecutive_failures} consecutive failures)"
                                )
                            else:
                                status.consecutive_failures = 0

                # Sleep for health check interval (default 5 minutes)
                await asyncio.sleep(self.config.get("health_check_interval", 300))

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in notification health monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
