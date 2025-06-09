"""
Notification system models for tracking sent notifications and delivery status.

This module contains Pydantic models for the notification system including
notification logs, delivery tracking, and template contexts.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class NotificationType(str, Enum):
    """Enumeration of notification types."""

    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class NotificationChannel(str, Enum):
    """Enumeration of notification channels."""

    SMTP = "smtp"
    SLACK = "slack"
    DISCORD = "discord"
    WEBHOOK = "webhook"
    SYSTEM = "system"


class NotificationStatus(str, Enum):
    """Enumeration of notification delivery status."""

    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"


class NotificationLog(BaseModel):
    """
    Model for tracking notification delivery attempts and results.

    This model is used for logging and auditing notification delivery
    across all channels and types.
    """

    id: str | None = Field(None, description="Unique notification ID")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Notification timestamp"
    )

    # Notification content
    title: str = Field(..., description="Notification title")
    message: str = Field(..., description="Notification message body")
    notification_type: NotificationType = Field(
        NotificationType.INFO, description="Type of notification"
    )

    # Delivery information
    channels: list[NotificationChannel] = Field(default_factory=list, description="Target channels")
    tags: list[str] = Field(default_factory=list, description="Notification tags")
    recipient: str | None = Field(None, description="Primary recipient (email, user ID, etc.)")

    # Status tracking
    status: NotificationStatus = Field(NotificationStatus.PENDING, description="Delivery status")
    delivery_attempts: int = Field(0, description="Number of delivery attempts")
    last_attempt: datetime | None = Field(None, description="Timestamp of last delivery attempt")

    # Results and errors
    success: bool = Field(False, description="Whether notification was successfully delivered")
    error_message: str | None = Field(None, description="Error message if delivery failed")
    delivery_details: dict[str, Any] = Field(
        default_factory=dict, description="Channel-specific delivery details"
    )

    # Template and context information
    template_name: str | None = Field(None, description="Template used for rendering")
    context_data: dict[str, Any] = Field(
        default_factory=dict, description="Template context data (sensitive data excluded)"
    )

    # Metadata
    source_component: str | None = Field(
        None, description="Component that triggered the notification"
    )
    correlation_id: str | None = Field(
        None, description="Correlation ID for tracking related notifications"
    )


class EmailNotificationContext(BaseModel):
    """
    Template context for email notifications.

    This model defines the standard context structure for email templates
    used in authentication and system notifications.
    """

    # Recipient information
    to_email: str = Field(..., description="Recipient email address")
    user_name: str | None = Field(None, description="Recipient display name")

    # Application branding
    app_name: str = Field("CoachIQ", description="Application name")
    app_logo_url: str | None = Field(None, description="Application logo URL")
    support_email: str = Field("support@coachiq.com", description="Support contact email")

    # Email content
    subject: str = Field(..., description="Email subject line")
    preheader: str | None = Field(None, description="Email preheader text")

    # Authentication-specific fields
    magic_link: str | None = Field(None, description="Magic link URL for authentication")
    verification_code: str | None = Field(None, description="Verification code")
    expires_minutes: int = Field(15, description="Link/code expiration time in minutes")

    # System notification fields
    system_component: str | None = Field(None, description="System component name")
    alert_level: str | None = Field(None, description="Alert severity level")
    action_required: bool = Field(False, description="Whether user action is required")
    action_url: str | None = Field(None, description="URL for required action")

    # Additional context data
    custom_data: dict[str, Any] = Field(default_factory=dict, description="Custom template data")


class MagicLinkContext(EmailNotificationContext):
    """
    Specialized context for magic link authentication emails.
    """

    magic_link: str = Field(..., description="Magic link URL for authentication")
    login_attempt_ip: str | None = Field(None, description="IP address of login attempt")
    login_attempt_location: str | None = Field(
        None, description="Geographic location of login attempt"
    )
    device_info: str | None = Field(None, description="Device/browser information")


class SystemNotificationContext(EmailNotificationContext):
    """
    Specialized context for system notification emails.
    """

    system_component: str = Field(..., description="System component name")
    alert_level: str = Field(..., description="Alert severity level")
    event_timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Event timestamp"
    )
    event_details: dict[str, Any] = Field(
        default_factory=dict, description="Event-specific details"
    )
    resolution_steps: list[str] = Field(
        default_factory=list, description="Suggested resolution steps"
    )


class NotificationTemplate(BaseModel):
    """
    Model for notification template metadata and configuration.
    """

    name: str = Field(..., description="Template name/identifier")
    display_name: str = Field(..., description="Human-readable template name")
    description: str | None = Field(None, description="Template description")

    # Template configuration
    template_type: str = Field("email", description="Template type (email, slack, etc.)")
    content_format: str = Field("html", description="Content format (html, text, markdown)")

    # Usage information
    category: str = Field("general", description="Template category (auth, system, user)")
    tags: list[str] = Field(default_factory=list, description="Template tags")

    # Validation and requirements
    required_context_fields: list[str] = Field(
        default_factory=list, description="Required context fields"
    )
    optional_context_fields: list[str] = Field(
        default_factory=list, description="Optional context fields"
    )

    # Template metadata
    version: str = Field("1.0", description="Template version")
    author: str | None = Field(None, description="Template author")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )


class NotificationPreferences(BaseModel):
    """
    Model for user notification preferences.

    This model will be used in the authentication system to store
    user preferences for different types of notifications.
    """

    user_id: str = Field(..., description="User identifier")

    # Channel preferences
    email_enabled: bool = Field(True, description="Enable email notifications")
    slack_enabled: bool = Field(False, description="Enable Slack notifications")
    discord_enabled: bool = Field(False, description="Enable Discord notifications")

    # Notification type preferences
    security_alerts: bool = Field(True, description="Receive security alerts")
    system_notifications: bool = Field(True, description="Receive system notifications")
    maintenance_notifications: bool = Field(False, description="Receive maintenance notifications")
    feature_announcements: bool = Field(False, description="Receive feature announcements")

    # Delivery preferences
    digest_mode: bool = Field(
        False, description="Receive digest instead of individual notifications"
    )
    digest_frequency: str = Field("daily", description="Digest frequency (hourly, daily, weekly)")
    quiet_hours_enabled: bool = Field(False, description="Enable quiet hours")
    quiet_hours_start: str | None = Field(None, description="Quiet hours start time (HH:MM)")
    quiet_hours_end: str | None = Field(None, description="Quiet hours end time (HH:MM)")

    # Metadata
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Preferences creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )


class NotificationChannelStatus(BaseModel):
    """
    Model for tracking notification channel health and status.
    """

    channel: NotificationChannel = Field(..., description="Notification channel")
    enabled: bool = Field(True, description="Whether channel is enabled")

    # Health information
    healthy: bool = Field(True, description="Whether channel is healthy")
    last_success: datetime | None = Field(None, description="Last successful delivery")
    last_failure: datetime | None = Field(None, description="Last delivery failure")
    consecutive_failures: int = Field(0, description="Number of consecutive failures")

    # Configuration status
    configured: bool = Field(False, description="Whether channel is properly configured")
    configuration_errors: list[str] = Field(
        default_factory=list, description="Configuration error messages"
    )

    # Performance metrics
    total_sent: int = Field(0, description="Total notifications sent")
    total_failures: int = Field(0, description="Total delivery failures")
    success_rate: float = Field(0.0, description="Success rate (0.0-1.0)")
    average_delivery_time: float | None = Field(
        None, description="Average delivery time in seconds"
    )

    # Status timestamps
    checked_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last status check timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )
