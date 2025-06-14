"""
Pydantic models for feature management system with safety classifications.

These models provide type safety and validation for the feature management system,
ensuring that safety-critical requirements are enforced at the schema level.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class SafetyClassification(str, Enum):
    """
    Safety classification levels for features, inspired by ISO 26262 ASIL levels.

    Each level has specific runtime behavior and safety requirements:
    - CRITICAL: System cannot operate safely without this feature
    - SAFETY_RELATED: Impacts safety but system can continue with limitations
    - POSITION_CRITICAL: Controls physical positioning that shouldn't change in emergencies
    - OPERATIONAL: Important for operation but not safety-critical
    - MAINTENANCE: Diagnostic and utility features
    """

    CRITICAL = "critical"
    """System cannot operate safely without this feature (ASIL C/D equivalent).

    Examples: can_interface, persistence, authentication
    - Failure requires immediate safe state transition
    - Cannot be toggled at runtime
    - Mandatory health monitoring
    """

    SAFETY_RELATED = "safety_related"
    """Impacts safety but system can continue with limitations (ASIL A/B equivalent).

    Examples: spartan_k2, advanced_diagnostics, firefly
    - Failure requires notification and may restrict functionality
    - Cannot be toggled at runtime
    - Health monitoring required
    """

    POSITION_CRITICAL = "position_critical"
    """Controls physical positioning that shouldn't change in emergencies.

    Examples: slide_control, awning_control, leveling_control
    - Safe state action: maintain current position, disable new commands
    - Cannot be toggled at runtime while devices are deployed
    - Position monitoring required
    """

    OPERATIONAL = "operational"
    """Important for operation but not safety-critical.

    Examples: performance_analytics, dashboard_aggregation, activity_tracking
    - Can be toggled at runtime with audit trail
    - Failure impacts functionality but not safety
    - Optional health monitoring
    """

    MAINTENANCE = "maintenance"
    """Diagnostic and utility features.

    Examples: log_history, api_docs, debugging tools
    - Can be toggled at runtime with audit trail
    - Minimal impact on system operation
    - Basic health monitoring
    """


class SafeStateAction(str, Enum):
    """Actions to take when entering safe state for different feature types."""

    MAINTAIN_POSITION = "maintain_position"
    """Maintain current physical position, disable movement commands."""

    CONTINUE_OPERATION = "continue_operation"
    """Continue normal operation (e.g., lighting, climate)."""

    STOP_OPERATION = "stop_operation"
    """Stop operation safely (e.g., pumps, generators)."""

    CONTROLLED_SHUTDOWN = "controlled_shutdown"
    """Perform controlled shutdown sequence."""

    EMERGENCY_STOP = "emergency_stop"
    """Immediate stop for emergency situations."""


class FeatureState(str, Enum):
    """
    Feature lifecycle states for health monitoring and management.

    States follow a defined lifecycle with clear transitions:
    - STOPPED -> INITIALIZING -> HEALTHY
    - HEALTHY -> DEGRADED -> FAILED
    - Any state -> MAINTENANCE (manual intervention)
    - FAILED -> SAFE_SHUTDOWN (for critical features)
    """

    STOPPED = "stopped"
    """Feature is not running and not initialized."""

    INITIALIZING = "initializing"
    """Feature is starting up and performing initialization."""

    HEALTHY = "healthy"
    """Feature is running normally with all functions available."""

    DEGRADED = "degraded"
    """Feature is partially functional or has non-critical issues."""

    FAILED = "failed"
    """Feature has failed and is non-functional."""

    SAFE_SHUTDOWN = "safe_shutdown"
    """Feature is performing controlled shutdown for safety."""

    MAINTENANCE = "maintenance"
    """Feature is intentionally offline for service."""


class FeatureDefinition(BaseModel):
    """
    Complete definition of a feature including safety requirements.

    This model validates the feature definition from YAML and ensures
    all safety-critical attributes are properly specified.
    """

    name: str = Field(..., description="Unique feature identifier")

    enabled_by_default: bool = Field(
        ...,
        alias="enabled",
        description="Default enabled state from YAML"
    )

    mandatory: bool = Field(
        default=False,
        description="If true, feature cannot be disabled and must start successfully"
    )

    safety_classification: SafetyClassification = Field(
        ...,
        description="Safety classification determining runtime behavior"
    )

    dependencies: list[str] = Field(
        default_factory=list,
        alias="depends_on",
        description="List of feature names this feature depends on"
    )

    maintain_state_on_failure: bool = Field(
        default=True,
        description="Whether to maintain current state when this feature fails"
    )

    safe_state_action: SafeStateAction = Field(
        default=SafeStateAction.MAINTAIN_POSITION,
        description="Action to take when entering safe state"
    )

    config: dict[str, Any] = Field(
        default_factory=dict,
        description="Feature-specific configuration parameters"
    )

    description: str = Field(
        default="",
        description="Human-readable description of the feature"
    )

    friendly_name: str = Field(
        default="",
        description="Human-readable display name"
    )

    # Health monitoring configuration
    health_check_interval_seconds: float = Field(
        default=5.0,
        ge=1.0,
        le=60.0,
        description="How often to check feature health"
    )

    health_timeout_seconds: float = Field(
        default=10.0,
        ge=1.0,
        le=30.0,
        description="Timeout for health check operations"
    )

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Ensure feature name is valid identifier."""
        if not v or not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Feature name must be alphanumeric with underscores/hyphens")
        return v

    @field_validator("dependencies")
    @classmethod
    def validate_dependencies(cls, v: list[str]) -> list[str]:
        """Ensure dependency names are valid."""
        for dep in v:
            if not dep or not dep.replace("_", "").replace("-", "").isalnum():
                raise ValueError(f"Invalid dependency name: {dep}")
        return v

    @field_validator("friendly_name", mode="before")
    @classmethod
    def generate_friendly_name(cls, v: str, info) -> str:
        """Generate friendly name from feature name if not provided."""
        if not v and "name" in info.data:
            return info.data["name"].replace("_", " ").title()
        return v or ""

    @field_validator("safe_state_action")
    @classmethod
    def validate_safe_state_action(cls, v: SafeStateAction, info) -> SafeStateAction:
        """Validate safe state action is appropriate for safety classification."""
        if "safety_classification" not in info.data:
            return v

        classification = info.data["safety_classification"]

        # Position-critical features should maintain position
        if classification == SafetyClassification.POSITION_CRITICAL:
            if v not in [SafeStateAction.MAINTAIN_POSITION, SafeStateAction.EMERGENCY_STOP]:
                raise ValueError(
                    f"Position-critical features must use maintain_position or emergency_stop, got: {v}"
                )

        return v

    def is_safety_critical(self) -> bool:
        """Check if this feature is considered safety-critical."""
        return self.safety_classification in [
            SafetyClassification.CRITICAL,
            SafetyClassification.SAFETY_RELATED,
            SafetyClassification.POSITION_CRITICAL
        ]

    def can_be_toggled_at_runtime(self) -> bool:
        """Check if this feature can be safely toggled at runtime."""
        return self.safety_classification in [
            SafetyClassification.OPERATIONAL,
            SafetyClassification.MAINTENANCE
        ]

    def requires_health_monitoring(self) -> bool:
        """Check if this feature requires active health monitoring."""
        return self.safety_classification in [
            SafetyClassification.CRITICAL,
            SafetyClassification.SAFETY_RELATED,
            SafetyClassification.POSITION_CRITICAL
        ]


class FeatureConfigurationSet(BaseModel):
    """
    Complete set of feature definitions loaded from YAML.

    This model validates the entire feature configuration and provides
    methods for querying and analyzing the feature set.
    """

    features: dict[str, FeatureDefinition] = Field(
        ...,
        description="Dictionary of feature name to feature definition"
    )

    @field_validator("features")
    @classmethod
    def validate_feature_dependencies(cls, v: dict[str, FeatureDefinition]) -> dict[str, FeatureDefinition]:
        """Validate that all feature dependencies exist."""
        feature_names = set(v.keys())

        for feature_name, feature_def in v.items():
            for dep in feature_def.dependencies:
                if dep not in feature_names:
                    raise ValueError(
                        f"Feature '{feature_name}' depends on '{dep}' which does not exist"
                    )

        return v

    def get_features_by_classification(self, classification: SafetyClassification) -> list[FeatureDefinition]:
        """Get all features with a specific safety classification."""
        return [
            feature for feature in self.features.values()
            if feature.safety_classification == classification
        ]

    def get_critical_features(self) -> list[FeatureDefinition]:
        """Get all safety-critical features."""
        return [
            feature for feature in self.features.values()
            if feature.is_safety_critical()
        ]

    def get_toggleable_features(self) -> list[FeatureDefinition]:
        """Get all features that can be toggled at runtime."""
        return [
            feature for feature in self.features.values()
            if feature.can_be_toggled_at_runtime()
        ]

    def validate_dependency_graph(self) -> None:
        """Validate that dependency graph has no cycles."""
        # Implementation of cycle detection using DFS
        WHITE, GRAY, BLACK = 0, 1, 2
        colors = dict.fromkeys(self.features.keys(), WHITE)

        def dfs(node: str) -> bool:
            if colors[node] == GRAY:
                return True  # Back edge found, cycle detected
            if colors[node] == BLACK:
                return False  # Already processed

            colors[node] = GRAY
            for dep in self.features[node].dependencies:
                if dfs(dep):
                    return True
            colors[node] = BLACK
            return False

        for feature_name in self.features.keys():
            if colors[feature_name] == WHITE:
                if dfs(feature_name):
                    raise ValueError(f"Circular dependency detected involving '{feature_name}'")

    def get_startup_order(self) -> list[str]:
        """Get the correct startup order based on dependencies."""
        # Topological sort implementation
        in_degree = dict.fromkeys(self.features.keys(), 0)

        # Calculate in-degrees
        for feature_def in self.features.values():
            for dep in feature_def.dependencies:
                in_degree[feature_def.name] += 1

        # Use queue for topological sort
        from collections import deque
        queue = deque([name for name, degree in in_degree.items() if degree == 0])
        result = []

        while queue:
            current = queue.popleft()
            result.append(current)

            # Update in-degrees for dependent features
            for feature_def in self.features.values():
                if current in feature_def.dependencies:
                    in_degree[feature_def.name] -= 1
                    if in_degree[feature_def.name] == 0:
                        queue.append(feature_def.name)

        if len(result) != len(self.features):
            raise ValueError("Circular dependency detected in feature graph")

        return result


class SafetyValidator:
    """
    Safety validation utility for feature state transitions and operations.

    Implements ISO 26262-inspired validation patterns for RV-C vehicle control systems.
    """

    # Valid state transitions based on safety requirements
    VALID_TRANSITIONS: dict[FeatureState, set[FeatureState]] = {
        FeatureState.STOPPED: {
            FeatureState.INITIALIZING,
            FeatureState.MAINTENANCE,
        },
        FeatureState.INITIALIZING: {
            FeatureState.HEALTHY,
            FeatureState.FAILED,
            FeatureState.STOPPED,
        },
        FeatureState.HEALTHY: {
            FeatureState.DEGRADED,
            FeatureState.FAILED,
            FeatureState.SAFE_SHUTDOWN,
            FeatureState.MAINTENANCE,
        },
        FeatureState.DEGRADED: {
            FeatureState.HEALTHY,      # Recovery possible
            FeatureState.FAILED,
            FeatureState.SAFE_SHUTDOWN,
            FeatureState.MAINTENANCE,
        },
        FeatureState.FAILED: {
            FeatureState.SAFE_SHUTDOWN,
            FeatureState.MAINTENANCE,
            FeatureState.STOPPED,      # For complete restart
        },
        FeatureState.SAFE_SHUTDOWN: {
            FeatureState.STOPPED,
            FeatureState.MAINTENANCE,
        },
        FeatureState.MAINTENANCE: {
            FeatureState.STOPPED,
            FeatureState.INITIALIZING,
            FeatureState.HEALTHY,      # Direct return from maintenance
        },
    }

    @classmethod
    def validate_state_transition(
        cls,
        from_state: FeatureState,
        to_state: FeatureState,
        safety_classification: SafetyClassification,
        feature_name: str = "unknown"
    ) -> tuple[bool, str]:
        """
        Validate if a state transition is allowed for a feature.

        Args:
            from_state: Current state
            to_state: Desired new state
            safety_classification: Safety classification of the feature
            feature_name: Name of the feature (for logging)

        Returns:
            Tuple of (is_valid, reason_if_invalid)
        """
        if from_state == to_state:
            return True, "No state change"

        valid_next_states = cls.VALID_TRANSITIONS.get(from_state, set())

        if to_state not in valid_next_states:
            return False, f"Invalid transition from {from_state.value} to {to_state.value}"

        # Additional safety checks for critical features
        if safety_classification == SafetyClassification.CRITICAL:
            # Critical features should not transition to FAILED without going through DEGRADED first
            # unless it's an emergency (INITIALIZING -> FAILED is allowed)
            if (from_state == FeatureState.HEALTHY and
                to_state == FeatureState.FAILED):
                return False, "Critical features must transition through DEGRADED before FAILED"

        # Position-critical features have additional restrictions
        if safety_classification == SafetyClassification.POSITION_CRITICAL:
            # Position-critical features should prefer SAFE_SHUTDOWN over FAILED
            if (from_state in [FeatureState.HEALTHY, FeatureState.DEGRADED] and
                to_state == FeatureState.FAILED):
                return False, "Position-critical features should use SAFE_SHUTDOWN instead of FAILED"

        return True, "Valid transition"

    @classmethod
    def get_safe_transition(
        cls,
        current_state: FeatureState,
        desired_state: FeatureState,
        safety_classification: SafetyClassification
    ) -> FeatureState:
        """
        Get a safe intermediate state if direct transition is not allowed.

        Args:
            current_state: Current state
            desired_state: Desired target state
            safety_classification: Safety classification of the feature

        Returns:
            Safe intermediate state or desired_state if direct transition is valid
        """
        is_valid, _ = cls.validate_state_transition(
            current_state, desired_state, safety_classification
        )

        if is_valid:
            return desired_state

        # Find safe intermediate state
        valid_next_states = cls.VALID_TRANSITIONS.get(current_state, set())

        # For critical failures, prefer DEGRADED as intermediate state
        if (desired_state == FeatureState.FAILED and
            FeatureState.DEGRADED in valid_next_states):
            return FeatureState.DEGRADED

        # For position-critical features, prefer SAFE_SHUTDOWN
        if (safety_classification == SafetyClassification.POSITION_CRITICAL and
            FeatureState.SAFE_SHUTDOWN in valid_next_states):
            return FeatureState.SAFE_SHUTDOWN

        # Default: return first valid state
        if valid_next_states:
            return next(iter(valid_next_states))

        return current_state  # No valid transition possible

    @classmethod
    def is_emergency_stop_required(
        cls,
        feature_state: FeatureState,
        safety_classification: SafetyClassification,
        failed_dependencies: set[str] = None
    ) -> bool:
        """
        Determine if emergency stop is required based on feature state and classification.

        Args:
            feature_state: Current state of the feature
            safety_classification: Safety classification
            failed_dependencies: Set of failed dependency names

        Returns:
            True if emergency stop should be triggered
        """
        failed_dependencies = failed_dependencies or set()

        # Critical features failing should trigger emergency stop
        if (safety_classification == SafetyClassification.CRITICAL and
            feature_state == FeatureState.FAILED):
            return True

        # Position-critical features with critical dependencies failed
        if (safety_classification == SafetyClassification.POSITION_CRITICAL and
            len(failed_dependencies) > 0):
            return True

        # Multiple safety-related features failing simultaneously
        if (safety_classification == SafetyClassification.SAFETY_RELATED and
            feature_state == FeatureState.FAILED and
            len(failed_dependencies) >= 2):
            return True

        return False

    @classmethod
    def get_required_safety_actions(
        cls,
        safety_classification: SafetyClassification,
        current_state: FeatureState,
        safe_state_action: SafeStateAction
    ) -> list[str]:
        """
        Get list of required safety actions for a feature in its current state.

        Args:
            safety_classification: Safety classification
            current_state: Current feature state
            safe_state_action: Configured safe state action

        Returns:
            List of required safety action descriptions
        """
        actions = []

        if current_state in [FeatureState.FAILED, FeatureState.SAFE_SHUTDOWN]:
            if safety_classification == SafetyClassification.CRITICAL:
                actions.extend([
                    "Notify system administrator immediately",
                    "Log all recent operations for forensic analysis",
                    "Attempt automatic recovery only if explicitly configured",
                ])

            if safety_classification == SafetyClassification.POSITION_CRITICAL:
                if safe_state_action == SafeStateAction.MAINTAIN_POSITION:
                    actions.extend([
                        "Maintain current physical positions",
                        "Disable all movement commands",
                        "Enable position monitoring only",
                        "Record current position state for recovery",
                    ])
                elif safe_state_action == SafeStateAction.EMERGENCY_STOP:
                    actions.extend([
                        "Execute immediate emergency stop",
                        "Log emergency stop reason and timestamp",
                        "Require manual intervention to resume",
                    ])

            if safety_classification == SafetyClassification.SAFETY_RELATED:
                actions.extend([
                    "Continue monitoring system health",
                    "Disable non-essential functionality",
                    "Provide degraded service where possible",
                ])

        return actions
