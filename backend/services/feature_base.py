"""
Base class for backend features with dependency management and health reporting.

This module provides the foundation for feature management with safety-critical
health monitoring and state management capabilities.

Example:
    >>> class MyFeature(Feature):
    ...     async def startup(self):
    ...         self._state = FeatureState.INITIALIZING
    ...         # Custom startup logic
    ...         self._state = FeatureState.HEALTHY
    ...     async def shutdown(self):
    ...         self._state = FeatureState.STOPPED
    ...     async def check_health(self) -> FeatureState:
    ...         # Custom health check logic
    ...         return self._state
    >>> f = MyFeature(name="test", enabled=True, core=False)
    >>> await f.check_health()
    <FeatureState.HEALTHY: 'healthy'>
"""

from abc import ABC, abstractmethod
from typing import Any

from backend.services.feature_models import FeatureState, SafetyValidator, SafetyClassification


class Feature(ABC):
    """
    Base class for backend features with state management and health monitoring.

    Features can declare dependencies on other features, which will be
    resolved during startup to ensure proper initialization order.

    Attributes:
        name: Unique identifier for the feature
        friendly_name: Human-readable display name for the feature
        enabled: Whether the feature is enabled
        core: Whether this is a core feature (safety-critical)
        config: Configuration options for the feature
        dependencies: List of feature names this feature depends on
        _state: Current state of the feature (FeatureState)
        _failed_dependencies: Set of dependencies that have failed
    """

    name: str
    friendly_name: str
    enabled: bool
    core: bool
    config: dict[str, Any]
    dependencies: list[str]
    _state: FeatureState
    _failed_dependencies: set[str]

    def __init__(
        self,
        name: str,
        enabled: bool = False,
        core: bool = False,
        config: dict[str, Any] | None = None,
        dependencies: list[str] | None = None,
        friendly_name: str | None = None,
        safety_classification: SafetyClassification | None = None,
        log_state_transitions: bool = True,
    ) -> None:
        """
        Initialize a Feature instance.

        Args:
            name: Unique identifier for the feature
            enabled: Whether the feature is enabled
            core: Whether this is a core feature (safety-critical)
            config: Configuration options for the feature
            dependencies: List of feature names this feature depends on
            friendly_name: Human-readable display name for the feature
            safety_classification: Safety classification for state validation
            log_state_transitions: Whether to log state transitions for audit
        """
        self.name = name
        self.friendly_name = friendly_name or name.replace("_", " ").title()
        self.enabled = enabled
        self.core = core
        self.config = config or {}
        self.dependencies = dependencies or []
        self._state = FeatureState.STOPPED
        self._failed_dependencies = set()

        # Safety-related attributes
        self._safety_classification = safety_classification or (
            SafetyClassification.CRITICAL if core else SafetyClassification.OPERATIONAL
        )
        self._log_state_transitions = log_state_transitions

    @abstractmethod
    async def startup(self) -> None:
        """
        Called on FastAPI startup if feature is enabled.

        Override this method to implement feature initialization.
        Should set state to INITIALIZING, then HEALTHY on success.
        """
        ...

    @abstractmethod
    async def shutdown(self) -> None:
        """
        Called on FastAPI shutdown if feature is enabled.

        Override this method to implement clean feature shutdown.
        Should set state to SAFE_SHUTDOWN, then STOPPED.
        """
        ...

    async def check_health(self) -> FeatureState:
        """
        Check current health of the feature.

        This method should be overridden by features that need custom
        health checking logic. Default implementation returns current state.

        Returns:
            Current FeatureState
        """
        return self._state

    @property
    def state(self) -> FeatureState:
        """Get current feature state."""
        return self._state

    @state.setter
    def state(self, new_state: FeatureState) -> None:
        """Set feature state with safety validation."""
        # Get safety classification for validation
        # Note: This requires the feature manager to provide this info
        # For now, we'll assume OPERATIONAL as default, but this should be injected
        safety_classification = getattr(self, '_safety_classification', SafetyClassification.OPERATIONAL)

        # Validate state transition
        is_valid, reason = SafetyValidator.validate_state_transition(
            self._state, new_state, safety_classification, self.name
        )

        if not is_valid:
            # Log the invalid transition attempt
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(
                "Invalid state transition blocked for feature '%s': %s. "
                "Current state: %s, Attempted state: %s",
                self.name, reason, self._state.value, new_state.value
            )

            # Get a safe intermediate state
            safe_state = SafetyValidator.get_safe_transition(
                self._state, new_state, safety_classification
            )

            if safe_state != new_state:
                logger.info(
                    "Using safe intermediate state for feature '%s': %s -> %s",
                    self.name, self._state.value, safe_state.value
                )
                self._state = safe_state
            else:
                # No safe transition available, keep current state
                logger.warning(
                    "No safe transition available for feature '%s', maintaining current state: %s",
                    self.name, self._state.value
                )
                return
        else:
            # Valid transition, proceed normally
            self._state = new_state

        # Log successful state transitions for audit trail
        if hasattr(self, '_log_state_transitions') and self._log_state_transitions:
            import logging
            logger = logging.getLogger(__name__)
            logger.info(
                "Feature '%s' state transition: %s (safety: %s)",
                self.name, self._state.value, safety_classification.value
            )

    @property
    def health(self) -> str:
        """
        Returns the health status of the feature (legacy compatibility).

        Maps FeatureState to legacy health strings.

        Returns:
            str: Health status string
        """
        state_to_health = {
            FeatureState.STOPPED: "healthy",  # Not running is OK if disabled
            FeatureState.INITIALIZING: "healthy",
            FeatureState.HEALTHY: "healthy",
            FeatureState.DEGRADED: "degraded",
            FeatureState.FAILED: "failed",
            FeatureState.SAFE_SHUTDOWN: "degraded",
            FeatureState.MAINTENANCE: "healthy",  # Intentional offline
        }
        return state_to_health.get(self._state, "failed")

    async def on_dependency_failed(self, dependency_name: str, dependency_state: FeatureState) -> None:
        """
        Called when a dependency has failed or degraded.

        Features can override this to implement custom handling when
        their dependencies fail.

        Args:
            dependency_name: Name of the failed dependency
            dependency_state: New state of the dependency
        """
        self._failed_dependencies.add(dependency_name)
        # Default behavior: if any critical dependency fails, we degrade
        if dependency_state == FeatureState.FAILED and self._state == FeatureState.HEALTHY:
            self._state = FeatureState.DEGRADED

    async def on_dependency_recovered(self, dependency_name: str) -> None:
        """
        Called when a dependency has recovered.

        Features can override this to implement recovery logic.

        Args:
            dependency_name: Name of the recovered dependency
        """
        self._failed_dependencies.discard(dependency_name)
        # If all dependencies are healthy and we're degraded, consider recovery
        if not self._failed_dependencies and self._state == FeatureState.DEGRADED:
            # Feature should implement its own recovery logic
            pass

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize the feature to a dictionary for status reporting.

        Returns:
            dict: Dictionary representation of the feature
        """
        return {
            "name": self.name,
            "friendly_name": self.friendly_name,
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


class GenericFeature(Feature):
    """
    Generic concrete implementation of Feature for config-driven features.
    Provides basic lifecycle methods with state management.
    """

    async def startup(self) -> None:
        """Generic startup sets state to HEALTHY."""
        self._state = FeatureState.INITIALIZING
        # Generic features have no special initialization
        self._state = FeatureState.HEALTHY

    async def shutdown(self) -> None:
        """Generic shutdown sets state to STOPPED."""
        self._state = FeatureState.SAFE_SHUTDOWN
        # Generic features have no special cleanup
        self._state = FeatureState.STOPPED
