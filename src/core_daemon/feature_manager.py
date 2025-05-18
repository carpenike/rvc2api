"""
Feature manager for optional backend integrations in rvc2api.

This module allows optional features (e.g., notifications, monitoring) to be registered,
enabled/disabled via config, and initialized at startup.
"""

import logging
import os

from core_daemon.feature_base import Feature
from core_daemon.github_update_checker import UpdateCheckerFeature
from core_daemon.uptimerobot import UptimeRobotFeature

logger = logging.getLogger(__name__)


# Registry of features by name
_registered_features: dict[str, Feature] = {}


def register_feature(feature: Feature):
    """Register a feature instance."""
    _registered_features[feature.name] = feature
    logger.info(f"Registered feature: {feature.name} (enabled={feature.enabled})")


def get_feature(name: str) -> Feature | None:
    return _registered_features.get(name)


def get_enabled_features() -> dict[str, Feature]:
    return {k: v for k, v in _registered_features.items() if v.enabled}


def get_all_features() -> dict[str, Feature]:
    return dict(_registered_features)


def get_core_features() -> dict[str, Feature]:
    return {k: v for k, v in _registered_features.items() if v.core}


def get_optional_features() -> dict[str, Feature]:
    return {k: v for k, v in _registered_features.items() if not v.core}


async def startup_all():
    for feature in get_enabled_features().values():
        logger.info(f"Starting feature: {feature.name}")
        await feature.startup()


async def shutdown_all():
    for feature in get_enabled_features().values():
        logger.info(f"Shutting down feature: {feature.name}")
        await feature.shutdown()


# --- Feature Registration Section ---
# Register core and optional features here.
#
# Core features (always enabled, always present in the API):
register_feature(Feature(name="canbus", enabled=True, core=True))  # CAN bus support
register_feature(Feature(name="web_ui", enabled=True, core=True))  # Web UI
register_feature(UpdateCheckerFeature())  # GitHub update checker (core background service)

# Optional features (enabled via environment variable or config):
register_feature(
    Feature(
        name="pushover",
        enabled=os.getenv("ENABLE_PUSHOVER", "0") == "1",
        core=False,
        config={
            "user_key": os.getenv("PUSHOVER_USER_KEY"),
            "api_token": os.getenv("PUSHOVER_API_TOKEN"),
        },
    )
)
register_feature(
    UptimeRobotFeature(
        name="uptimerobot",
        enabled=os.getenv("ENABLE_UPTIMEROBOT", "0") == "1",
        core=False,
        config={
            "api_key": os.getenv("UPTIMEROBOT_API_KEY"),
        },
    )
)

# --- Core background services (not managed as features) ---
# The following are always-on infrastructure/background services, not registered as features:
# - GitHub update checker (github_update_checker.py): provides update/version info for the API/UI
# - WebSocket/log streaming: managed as part of the core app
# - Metrics/Prometheus: provided via middleware
#
# If you want to make any of these toggleable, you can refactor them as Feature subclasses
# and register here.
#
# Add more features as needed following this pattern.
