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
        colors = {name: WHITE for name in self.features.keys()}

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
        in_degree = {name: 0 for name in self.features.keys()}

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
