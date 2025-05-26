"""
Entity Models

Pydantic models for entity management and control operations.
These models handle entity state, control commands, and response validation.
"""

from pydantic import BaseModel, Field


class Entity(BaseModel):
    """Represents the state and metadata of a monitored RV-C entity."""

    entity_id: str
    value: dict[str, str]
    raw: dict[str, int]
    state: str
    timestamp: float
    suggested_area: str | None = "Unknown"
    device_type: str | None = "unknown"
    capabilities: list[str] | None = []
    friendly_name: str | None = None
    groups: list[str] | None = Field(default_factory=list)


class ControlCommand(BaseModel):
    """Defines the structure for sending control commands to an entity, typically a light."""

    command: str
    state: str | None = Field(
        None, description="Target state: 'on' or 'off'. Required only for 'set' command."
    )
    brightness: int | None = Field(
        None,
        ge=0,
        le=100,
        description=(
            "Brightness percent (0-100). Only used when command is 'set' and state is 'on'."
        ),
    )


class ControlEntityResponse(BaseModel):
    """Response model for individual entity control commands, confirming the action taken."""

    status: str
    entity_id: str
    command: str
    state: str
    brightness: int
    action: str


class SuggestedMapping(BaseModel):
    """
    Provides a suggested mapping for an unmapped device instance
    based on existing configurations.
    """

    instance: str
    name: str
    suggested_area: str | None = None
