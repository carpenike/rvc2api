"""
Authentication feature registration.

This module provides the factory function for creating authentication feature instances
with the feature management system.
"""

import logging

from backend.integrations.auth.feature import AuthenticationFeature

logger = logging.getLogger(__name__)


def register_authentication_feature(**kwargs) -> AuthenticationFeature:
    """
    Factory function to create and configure an authentication feature instance.

    Args:
        **kwargs: Additional keyword arguments for feature configuration

    Returns:
        AuthenticationFeature: Configured authentication feature instance
    """
    logger.info("Registering authentication feature")

    try:
        feature = AuthenticationFeature(**kwargs)
        logger.info("Authentication feature registered successfully")
        return feature

    except Exception as e:
        logger.error(f"Failed to register authentication feature: {e}")
        raise
