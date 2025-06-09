"""
Notification Feature Registration

Registration module for the notification feature following the established
feature management patterns.
"""

from backend.integrations.notifications.feature import NotificationFeature


def register_notification_feature(**kwargs) -> NotificationFeature:
    """
    Factory function to create and configure a notification feature instance.

    Args:
        **kwargs: Additional keyword arguments for feature configuration

    Returns:
        NotificationFeature: Configured notification feature instance
    """
    import logging

    logger = logging.getLogger(__name__)
    logger.info("Registering notification feature")

    try:
        feature = NotificationFeature(**kwargs)
        logger.info("Notification feature registered successfully")
        return feature

    except Exception as e:
        logger.error(f"Failed to register notification feature: {e}")
        raise
