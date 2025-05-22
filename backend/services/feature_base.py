"""
Base class for backend features with dependency management and health reporting.

This is a proof-of-concept implementation of the feature management system
described in the backend refactoring specification.

Example:
    >>> class MyFeature(Feature):
    ...     async def startup(self):
    ...         # Custom startup logic
    ...         pass
    ...     async def shutdown(self):
    ...         pass
    ...     @property
    ...     def health(self) -> str:
    ...         return "healthy" if self.enabled else "disabled"
    >>> f = MyFeature(name="test", enabled=True, core=False)
    >>> f.health
    'healthy'
"""

from abc import ABC, abstractmethod
from typing import Any


class Feature(ABC):
    """
    Base class for backend features (core or optional).
    Provides lifecycle methods, configuration, and health reporting.

    Features can declare dependencies on other features, which will be
    resolved during startup to ensure proper initialization order.

    Attributes:
        name: Unique identifier for the feature
        enabled: Whether the feature is enabled
        core: Whether this is a core feature (always enabled)
        config: Configuration options for the feature
        dependencies: List of feature names this feature depends on
    """

    name: str
    enabled: bool
    core: bool
    config: dict[str, Any]
    dependencies: list[str]

    def __init__(
        self,
        name: str,
        enabled: bool = False,
        core: bool = False,
        config: dict[str, Any] | None = None,
        dependencies: list[str] | None = None,
    ) -> None:
        """
        Initialize a Feature instance.

        Args:
            name: Unique identifier for the feature
            enabled: Whether the feature is enabled
            core: Whether this is a core feature (always enabled)
            config: Configuration options for the feature
            dependencies: List of feature names this feature depends on
        """
        self.name = name
        self.enabled = enabled
        self.core = core
        self.config = config or {}
        self.dependencies = dependencies or []

    @abstractmethod
    async def startup(self) -> None:
        """
        Called on FastAPI startup if feature is enabled.

        Override this method to implement feature initialization.
        """
        ...

    @abstractmethod
    async def shutdown(self) -> None:
        """
        Called on FastAPI shutdown if feature is enabled.

        Override this method to implement clean feature shutdown.
        """
        ...

    @property
    @abstractmethod
    def health(self) -> str:
        """
        Returns the health status of the feature.

        Valid return values:
        - "disabled": Feature is not enabled
        - "healthy": Feature is functioning correctly
        - "degraded": Feature has non-critical issues
        - "unhealthy": Feature is not functioning correctly
        - "unknown": Status cannot be determined (default)

        Returns:
            str: Health status string
        """
        ...

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize the feature to a dictionary for status reporting.

        Returns:
            dict: Dictionary representation of the feature
        """
        return {
            "name": self.name,
            "enabled": self.enabled,
            "core": self.core,
            "config": self.config,
            "dependencies": self.dependencies,
            "health": self.health,
        }

    def __str__(self) -> str:
        """String representation of the feature for logging."""
        return f"Feature(name={self.name}, enabled={self.enabled}, core={self.core})"

    def __repr__(self) -> str:
        """Debug representation of the feature."""
        return (
            f"<Feature name={self.name!r} enabled={self.enabled!r} core={self.core!r} "
            f"dependencies={self.dependencies!r}>"
        )
