"""
Feature management service for rvc2api.

This module provides a service class for managing features and feature flags
in the rvc2api backend. It manages feature registration, dependency resolution,
lifecycle (startup/shutdown), and status reporting.

Example:
    >>> manager = FeatureManager()
    >>> feature = Feature(name="test", enabled=True, core=True)
    >>> manager.register_feature(feature)
    >>> manager.is_enabled("test")
    True
"""

import logging
from pathlib import Path
from typing import Any

from backend.core.events import get_event_bus
from backend.services.feature_base import Feature

logger = logging.getLogger(__name__)


class FeatureManager:
    """
    Service for managing feature flags and lifecycle.

    This class provides a centralized registry for features, handles
    dependency resolution and startup/shutdown ordering, and provides
    methods for checking if features are enabled.

    Features are registered with the manager and can be queried by name.
    """

    def __init__(self) -> None:
        """
        Initialize the feature manager.
        """
        self._features: dict[str, Feature] = {}
        self._audit_log: list[dict[str, Any]] = []

    def register_feature(self, feature: Feature) -> None:
        """
        Register a feature with the manager.

        Args:
            feature: The feature to register

        Raises:
            ValueError: If a feature with the same name is already registered
        """
        if feature.name in self._features:
            logger.warning(f"Feature '{feature.name}' is already registered. Skipping.")
            raise ValueError(f"Feature '{feature.name}' is already registered.")
        self._features[feature.name] = feature
        logger.info(f"Registered feature: {feature.name} (enabled={feature.enabled})")
        get_event_bus().publish(
            "feature_registered",
            {"name": feature.name, "enabled": feature.enabled, "core": feature.core},
        )

    def unregister_feature(self, feature_name: str) -> None:
        """
        Unregister a feature by name.

        Args:
            feature_name: The name of the feature to remove
        """
        if feature_name in self._features:
            del self._features[feature_name]
            logger.info(f"Unregistered feature: {feature_name}")
            get_event_bus().publish("feature_unregistered", {"name": feature_name})

    def is_enabled(self, feature_name: str) -> bool:
        """
        Check if a feature is enabled.

        Args:
            feature_name: The name of the feature to check

        Returns:
            True if the feature exists and is enabled, False otherwise
        """
        feature = self._features.get(feature_name)
        return feature is not None and feature.enabled

    def get_feature(self, name: str) -> Feature | None:
        """
        Get a feature by name.

        Args:
            name: The name of the feature to get

        Returns:
            The feature if found, None otherwise
        """
        return self._features.get(name)

    def get_all_features(self) -> dict[str, Feature]:
        """
        Get all registered features.

        Returns:
            Dictionary of feature name to feature
        """
        return dict(self._features)

    def get_enabled_features(self) -> dict[str, Feature]:
        """
        Get all enabled features.

        Returns:
            Dictionary of enabled feature name to feature
        """
        return {k: v for k, v in self._features.items() if v.enabled}

    def get_core_features(self) -> dict[str, Feature]:
        """
        Get all core features.

        Returns:
            Dictionary of core feature name to feature
        """
        return {k: v for k, v in self._features.items() if getattr(v, "core", False)}

    def get_optional_features(self) -> dict[str, Feature]:
        """
        Get all optional (non-core) features.

        Returns:
            Dictionary of optional feature name to feature
        """
        return {k: v for k, v in self._features.items() if not getattr(v, "core", False)}

    def feature_status_summary(self) -> dict[str, dict[str, Any]]:
        """
        Get a summary of all features and their status.

        Returns:
            Dictionary mapping feature name to status dict
        """
        return {
            name: {"enabled": feature.enabled, "core": getattr(feature, "core", False)}
            for name, feature in self._features.items()
        }

    def enable_feature(self, feature_name: str) -> None:
        """
        Enable a feature at runtime.

        Args:
            feature_name: The name of the feature to enable
        """
        feature = self._features.get(feature_name)
        if feature and not feature.enabled:
            feature.enabled = True
            logger.info(f"Feature enabled at runtime: {feature_name}")
            self._audit_log.append({"event": "enabled", "feature": feature_name})
            get_event_bus().publish("feature_enabled", {"name": feature_name})

    def disable_feature(self, feature_name: str) -> None:
        """
        Disable a feature at runtime.

        Args:
            feature_name: The name of the feature to disable
        """
        feature = self._features.get(feature_name)
        if feature and feature.enabled:
            feature.enabled = False
            logger.info(f"Feature disabled at runtime: {feature_name}")
            self._audit_log.append({"event": "disabled", "feature": feature_name})
            get_event_bus().publish("feature_disabled", {"name": feature_name})

    def reload_features_from_config(self, settings: Any) -> None:
        """
        Reload feature states/configs from a settings/config object.

        Args:
            settings: The application settings/config object
        """
        logger.info("Reloading features from config...")
        # Example: update feature enabled state from settings
        for name, feature in self._features.items():
            config_key = f"enable_{name}"
            if hasattr(settings, config_key):
                new_enabled = getattr(settings, config_key)
                if feature.enabled != new_enabled:
                    if new_enabled:
                        self.enable_feature(name)
                    else:
                        self.disable_feature(name)
        self._audit_log.append({"event": "reload", "details": str(settings)})

    def validate_dependencies(self) -> None:
        """
        Validate feature dependencies and raise if cycles are detected.

        Raises:
            ValueError: If a circular dependency is found
        """
        self._resolve_dependencies()

    def sync_with_external_provider(self) -> None:
        """
        Hook for syncing feature states with an external feature flag provider.
        Override or extend this method to integrate with LaunchDarkly, Unleash, etc.
        """
        pass

    @property
    def audit_log(self) -> list[dict[str, Any]]:
        """
        Get the in-memory audit log of feature state changes.

        Returns:
            List of audit log events
        """
        return self._audit_log

    def _resolve_dependencies(self) -> list[str]:
        """
        Resolve feature dependencies into a startup order.

        Performs a topological sort of the feature dependency graph to
        determine the correct order to initialize features.

        Returns:
            List of feature names in dependency order

        Raises:
            ValueError: If circular dependencies are detected
        """
        # Create a copy of the dependency graph
        graph: dict[str, set[str]] = {}
        for name, feature in self._features.items():
            if not feature.enabled:
                continue

            # Only include dependencies on enabled features
            deps = {
                d for d in feature.dependencies if d in self._features and self._features[d].enabled
            }
            graph[name] = deps

        # Perform topological sort
        result: list[str] = []
        temp_visited: set[str] = set()
        perm_visited: set[str] = set()

        def visit(node: str) -> None:
            if node in perm_visited:
                return

            if node in temp_visited:
                cycle_path = " -> ".join([node, *list(temp_visited)])
                raise ValueError(f"Circular dependency detected: {cycle_path}")

            temp_visited.add(node)
            for dep in graph.get(node, set()):
                visit(dep)
            temp_visited.remove(node)
            perm_visited.add(node)
            result.append(node)

        for node in graph:
            visit(node)

        return result

    async def startup(self) -> None:
        """
        Start all enabled features in dependency order.

        Resolves feature dependencies and starts each enabled feature
        in the correct order.
        """
        logger.info("Starting features...")

        try:
            startup_order = self._resolve_dependencies()

            for name in startup_order:
                feature = self._features[name]
                logger.info(f"Starting feature: {name}")
                await feature.startup()

                get_event_bus().publish("feature_started", {"name": name, "health": feature.health})
        except ValueError as e:
            logger.error(f"Feature startup failed: {e}")
            raise

        logger.info("All features started")

    async def shutdown(self) -> None:
        """
        Shut down all enabled features in reverse dependency order.
        """
        logger.info("Shutting down features...")

        # Shutdown in reverse dependency order
        try:
            shutdown_order = self._resolve_dependencies()
            shutdown_order.reverse()  # Reverse for shutdown

            for name in shutdown_order:
                feature = self._features[name]
                logger.info(f"Shutting down feature: {name}")
                await feature.shutdown()

                get_event_bus().publish("feature_stopped", {"name": name})
        except ValueError as e:
            logger.error(f"Feature shutdown error: {e}")

        logger.info("All features shut down")

    @classmethod
    def from_yaml(cls, yaml_path: str | Path) -> "FeatureManager":
        """
        Create a FeatureManager instance from a YAML config file.

        Args:
            yaml_path: Path to the YAML file containing feature definitions

        Returns:
            FeatureManager instance with features loaded from config
        """
        import yaml  # local import to avoid global import if not needed

        from backend.services.feature_base import GenericFeature

        with open(yaml_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)
        manager = cls()
        for name, data in config.items():
            feature = GenericFeature(
                name=name,
                enabled=bool(data.get("enabled", False)),
                core=bool(data.get("core", False)),
                config=data,
                dependencies=data.get("depends_on", []),
            )
            manager.register_feature(feature)
        return manager


# Global instance for use with dependency injection
_feature_manager: FeatureManager | None = None


def get_feature_manager(
    settings: Any = None,
) -> FeatureManager:
    """
    Dependency provider for FeatureManager.

    Loads feature definitions from YAML config for maintainability and extensibility.

    Args:
        settings: Application settings

    Returns:
        Initialized FeatureManager instance
    """
    global _feature_manager
    from backend.core.config import get_settings  # local import to avoid circular import

    if settings is None:
        settings = get_settings()

    if _feature_manager is None:
        yaml_path = Path(__file__).parent / "feature_flags.yaml"
        _feature_manager = FeatureManager.from_yaml(yaml_path)
        # Optionally reload feature states from settings/env
        _feature_manager.reload_features_from_config(settings)

    return _feature_manager
