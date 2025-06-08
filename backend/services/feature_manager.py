"""
Feature management for backend services.

Handles feature registration, dependency resolution, startup, and shutdown.
"""

import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any, ClassVar

import yaml

from backend.services.feature_base import GenericFeature

logger = logging.getLogger(__name__)


class FeatureManager:
    """
    Manages features, their dependencies, and lifecycle (startup/shutdown).
    """

    _feature_factories: ClassVar[dict[str, Callable[..., Any]]] = {}

    def __init__(self) -> None:
        self._features: dict[str, Any] = {}

    def register_feature(self, feature: Any) -> None:
        """
        Register a feature instance.

        Args:
            feature: Feature instance to register
        """
        self._features[feature.name] = feature

    @property
    def features(self) -> dict[str, Any]:
        """
        Returns all registered features.
        """
        return self._features

    def is_enabled(self, feature_name: str) -> bool:
        """
        Check if a feature is enabled.

        Args:
            feature_name: Name of the feature to check

        Returns:
            True if the feature exists and is enabled, False otherwise
        """
        feature = self._features.get(feature_name)
        return feature is not None and getattr(feature, "enabled", False)

    def get_feature(self, feature_name: str) -> Any | None:
        """
        Get a feature instance by name.

        Args:
            feature_name: Name of the feature to retrieve

        Returns:
            Feature instance if found, None otherwise
        """
        return self._features.get(feature_name)

    def get_all_features(self) -> dict[str, Any]:
        """
        Get all registered features.

        Returns:
            Dictionary of feature name to feature instance
        """
        return self._features.copy()

    def get_enabled_features(self) -> dict[str, Any]:
        """
        Get all enabled features.

        Returns:
            Dictionary of enabled feature name to feature instance
        """
        return {
            name: feature
            for name, feature in self._features.items()
            if getattr(feature, "enabled", False)
        }

    def get_core_features(self) -> dict[str, Any]:
        """
        Get all core features.

        Returns:
            Dictionary of core feature name to feature instance
        """
        return {
            name: feature
            for name, feature in self._features.items()
            if getattr(feature, "core", False)
        }

    def get_optional_features(self) -> dict[str, Any]:
        """
        Get all optional (non-core) features.

        Returns:
            Dictionary of optional feature name to feature instance
        """
        return {
            name: feature
            for name, feature in self._features.items()
            if not getattr(feature, "core", False)
        }

    def update_feature_state(self, feature_name: str, enabled: bool) -> bool:
        """
        Update feature enabled state at runtime.

        Args:
            feature_name: Name of feature to update
            enabled: New enabled state

        Returns:
            True if updated successfully, False if feature not found
        """
        feature = self._features.get(feature_name)
        if not feature:
            return False

        if feature.enabled != enabled:
            logger.info(
                f"Updating feature '{feature_name}' enabled state: {feature.enabled} -> {enabled}"
            )
            feature.enabled = enabled

        return True

    def get_configuration_metadata(self) -> dict[str, Any]:
        """Get metadata about current configuration."""
        return {
            "total_features": len(self._features),
            "enabled_features": len(self.get_enabled_features()),
            "core_features": len(self.get_core_features()),
            "feature_dependencies": {
                name: getattr(feature, "dependencies", [])
                for name, feature in self._features.items()
            },
        }

    def _resolve_dependencies(self) -> list[str]:
        """
        Resolve feature dependencies using topological sort.

        Returns:
            List of feature names in dependency order.

        Raises:
            ValueError: If a cyclic dependency is detected.
        """
        graph: dict[str, list[str]] = {}
        for name, feature in self._features.items():
            graph[name] = feature.dependencies or []
        visited: set[str] = set()
        temp: set[str] = set()
        result: list[str] = []

        def visit(node: str) -> None:
            if node in temp:
                raise ValueError(f"Cyclic dependency detected at '{node}'")
            if node not in visited:
                temp.add(node)
                for dep in graph.get(node, []):
                    if dep not in self._features:
                        raise ValueError(f"Missing dependency '{dep}' for feature '{node}'")
                    visit(dep)
                temp.remove(node)
                visited.add(node)
                result.append(node)

        for node in graph:
            visit(node)
        return result

    async def startup(self) -> None:
        """
        Start all enabled features in dependency order.

        Resolves feature dependencies and starts each enabled feature in the correct order.
        """
        logger.info("Starting features...")
        try:
            order = self._resolve_dependencies()
            for name in order:
                feature = self._features[name]
                if getattr(feature, "enabled", False):
                    logger.info(f"Starting feature: {name}")
                    if hasattr(feature, "startup"):
                        await feature.startup()
        except ValueError as e:
            logger.error(f"Feature startup error: {e}")
            raise
        logger.info("All features started")

    async def shutdown(self) -> None:
        """
        Shut down all enabled features in reverse dependency order.
        """
        logger.info("Shutting down features...")
        try:
            order = self._resolve_dependencies()[::-1]  # Reverse for shutdown
            for name in order:
                feature = self._features[name]
                if getattr(feature, "enabled", False):
                    logger.info(f"Shutting down feature: {name}")
                    try:
                        if hasattr(feature, "shutdown"):
                            await feature.shutdown()
                        logger.debug(f"Feature {name} shut down successfully")
                    except Exception as e:
                        logger.error(f"Error shutting down feature {name}: {e}")
                        # Continue with other features even if one fails
        except ValueError as e:
            logger.error(f"Feature shutdown error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during feature shutdown: {e}")
        logger.info("All features shut down")

    @classmethod
    def register_feature_factory(cls, feature_name: str, factory_func: Callable[..., Any]) -> None:
        """
        Register a factory function for a specific feature.

        Args:
            feature_name: Name of the feature
            factory_func: Function that creates a feature instance
        """
        cls._feature_factories[feature_name] = factory_func

    @classmethod
    def from_yaml(cls, yaml_path: str | Path) -> "FeatureManager":
        """
        Create a FeatureManager instance from a YAML config file.

        Args:
            yaml_path: Path to the YAML file containing feature definitions

        Returns:
            FeatureManager instance with features loaded from config
        """
        with open(yaml_path, encoding="utf-8") as f:
            config = yaml.safe_load(f)
        manager = cls()
        for name, data in config.items():
            if name in cls._feature_factories:
                feature = cls._feature_factories[name](
                    name=name,
                    enabled=bool(data.get("enabled", False)),
                    core=bool(data.get("core", False)),
                    config=data,
                    dependencies=data.get("depends_on", []),
                    friendly_name=data.get("friendly_name"),
                )
            else:
                feature = GenericFeature(
                    name=name,
                    enabled=bool(data.get("enabled", False)),
                    core=bool(data.get("core", False)),
                    config=data,
                    dependencies=data.get("depends_on", []),
                    friendly_name=data.get("friendly_name"),
                )
            manager.register_feature(feature)
        return manager

    def reload_features_from_config(self, settings: Any) -> None:
        """
        Reload feature states from application settings or environment variables.

        This method allows runtime overriding of feature states based on configuration.
        Environment variables take precedence over YAML settings.

        Args:
            settings: Application settings containing feature overrides
        """
        import os

        logger.info("Reloading feature states from configuration")

        for feature_name, feature in self._features.items():
            # First check for new standardized environment variable pattern (RVC2API_FEATURES__*)
            standardized_env_var = f"RVC2API_FEATURES__ENABLE_{feature_name.upper()}"
            standardized_env_value = os.getenv(standardized_env_var)

            # Fall back to legacy pattern for backward compatibility
            legacy_env_var = f"ENABLE_{feature_name.upper()}"
            legacy_env_value = os.getenv(legacy_env_var)

            env_value = standardized_env_value or legacy_env_value
            env_var_used = standardized_env_var if standardized_env_value else legacy_env_var

            if env_value is not None:
                # Environment variable found - use it to override feature state
                enabled = env_value.lower() in ("1", "true", "yes", "on")
                if feature.enabled != enabled:
                    logger.info(
                        f"Overriding feature '{feature_name}' enabled state: {feature.enabled} -> {enabled} (from {env_var_used})"
                    )
                    feature.enabled = enabled

            # Check for settings-based feature overrides using the standardized features config
            elif hasattr(settings, "features"):
                # Map common feature names to settings attributes
                feature_mapping = {
                    "pushover": "enable_pushover",
                    "uptimerobot": "enable_uptimerobot",
                    "github_update_checker": "enable_notifications",  # approximate mapping
                    "log_history": "enable_metrics",  # approximate mapping
                    "log_streaming": "enable_metrics",  # approximate mapping
                    "api_docs": "enable_api_docs",
                    "websocket": "enable_metrics",  # core feature, use metrics as proxy
                }

                settings_attr = feature_mapping.get(feature_name)
                if settings_attr and hasattr(settings.features, settings_attr):
                    enabled = getattr(settings.features, settings_attr)
                    if feature.enabled != enabled:
                        logger.info(
                            f"Overriding feature '{feature_name}' enabled state: {feature.enabled} -> {enabled} (from settings.features.{settings_attr})"
                        )
                        feature.enabled = enabled

            # Legacy fallback for old feature_flags structure
            elif hasattr(settings, "feature_flags") and isinstance(settings.feature_flags, dict):
                feature_config = settings.feature_flags.get(feature_name)
                if feature_config and "enabled" in feature_config:
                    enabled = bool(feature_config["enabled"])
                    if feature.enabled != enabled:
                        logger.info(
                            f"Overriding feature '{feature_name}' enabled state: {feature.enabled} -> {enabled} (from legacy settings)"
                        )
                        feature.enabled = enabled


# Register EntityManager factory
def _create_entity_manager_feature(**kwargs):
    """Factory function for EntityManagerFeature."""
    from backend.core.entity_feature import EntityManagerFeature

    return EntityManagerFeature(**kwargs)


# Register Persistence factory
def _create_persistence_feature(**kwargs):
    """Factory function for PersistenceFeature."""
    from backend.core.persistence_feature import PersistenceFeature

    return PersistenceFeature(**kwargs)


FeatureManager.register_feature_factory("entity_manager", _create_entity_manager_feature)
FeatureManager.register_feature_factory("persistence", _create_persistence_feature)


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
    from backend.core.config import (
        get_settings,
    )

    if settings is None:
        settings = get_settings()

    if _feature_manager is None:
        yaml_path = Path(__file__).parent / "feature_flags.yaml"
        _feature_manager = FeatureManager.from_yaml(yaml_path)
        # Optionally reload feature states from settings/env
        _feature_manager.reload_features_from_config(settings)

    return _feature_manager
