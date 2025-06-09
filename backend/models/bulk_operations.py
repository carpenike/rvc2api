"""
Bulk Operations Models

Pydantic models for bulk operations and device groups.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class BulkOperationModel(BaseModel):
    """Model for bulk operations."""

    id: str = Field(..., description="Unique operation identifier")
    operation_type: str = Field(..., description="Type of operation")
    targets: list[str] = Field(..., description="List of target device IDs")
    payload: dict[str, Any] = Field(..., description="Operation payload")
    description: str | None = Field(None, description="Human-readable description")
    status: str = Field(..., description="Operation status")
    total_tasks: int = Field(..., description="Total number of tasks")
    success_count: int = Field(default=0, description="Number of successful operations")
    failure_count: int = Field(default=0, description="Number of failed operations")
    failed_devices: list[dict[str, Any]] = Field(
        default_factory=list, description="List of failed devices with errors"
    )
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return self.model_dump()


class DeviceGroupModel(BaseModel):
    """Model for device groups."""

    id: str = Field(..., description="Unique group identifier")
    name: str = Field(..., description="Group name")
    description: str | None = Field(None, description="Group description")
    device_ids: list[str] = Field(..., description="List of device IDs in the group")
    exemptions: dict[str, Any] = Field(
        default_factory=dict, description="Exemptions for specific operations"
    )
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return self.model_dump()
