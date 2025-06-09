"""
Bulk Operations API Router

FastAPI router for bulk device operations and group management.
Implements asynchronous job-based operations with WebSocket progress updates.

Routes:
- POST /bulk-operations: Create and execute bulk operations
- GET /bulk-operations/{operation_id}: Get bulk operation status
- GET /groups: List device groups
- POST /groups: Create new device group
- PUT /groups/{group_id}: Update device group
- DELETE /groups/{group_id}: Delete device group
- POST /groups/{group_id}/execute: Execute group as bulk operation
"""

import logging
import uuid
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from backend.core.dependencies import (
    get_bulk_operations_service,
    get_feature_manager_from_request,
)

logger = logging.getLogger(__name__)

# Create the router
router = APIRouter(prefix="/api/bulk-operations", tags=["bulk-operations"])


def _check_bulk_operations_feature_enabled(request: Request) -> None:
    """
    Check if the bulk_operations feature is enabled.

    Raises HTTPException with 404 status if the feature is disabled.
    """
    feature_manager = get_feature_manager_from_request(request)
    if not feature_manager.is_enabled("bulk_operations"):
        raise HTTPException(
            status_code=404,
            detail="bulk_operations feature is disabled",
        )


# Pydantic Models
class BulkOperationPayload(BaseModel):
    """Payload for bulk operations."""

    command: str = Field(..., description="Command to execute")
    state: str | None = Field(None, description="Target state (on/off)")
    brightness: int | None = Field(None, ge=0, le=100, description="Brightness level (0-100)")
    value: Any | None = Field(None, description="Generic value for custom commands")
    unit: str | None = Field(None, description="Unit for the value")


class BulkOperationRequest(BaseModel):
    """Request model for bulk operations."""

    operation_type: str = Field(
        ..., description="Type of operation (state_change, configuration_change, status_check)"
    )
    targets: list[str] = Field(..., min_items=1, description="List of device IDs to target")
    payload: BulkOperationPayload = Field(..., description="Operation payload")
    description: str | None = Field(None, description="Human-readable description of the operation")


class BulkOperationResponse(BaseModel):
    """Response model for bulk operation creation."""

    status: str = Field(..., description="Operation status")
    operation_id: str = Field(..., description="Unique operation identifier")
    total_tasks: int = Field(..., description="Total number of devices to process")
    queued_at: datetime = Field(..., description="When the operation was queued")


class DeviceGroupRequest(BaseModel):
    """Request model for device group creation/update."""

    name: str = Field(..., min_length=1, max_length=100, description="Group name")
    description: str | None = Field(None, max_length=500, description="Group description")
    device_ids: list[str] = Field(..., min_items=1, description="List of device IDs in the group")
    exemptions: dict[str, Any] | None = Field(
        None, description="Exemptions for specific operations"
    )


class DeviceGroup(BaseModel):
    """Device group model."""

    id: str = Field(..., description="Unique group identifier")
    name: str = Field(..., description="Group name")
    description: str | None = Field(None, description="Group description")
    device_ids: list[str] = Field(..., description="List of device IDs in the group")
    exemptions: dict[str, Any] | None = Field(
        None, description="Exemptions for specific operations"
    )
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


@router.post(
    "/",
    response_model=BulkOperationResponse,
    summary="Create bulk operation",
    description="Create and execute a bulk operation on multiple devices.",
)
async def create_bulk_operation(
    request: Request,
    operation_request: BulkOperationRequest,
    bulk_service: Annotated[Any, Depends(get_bulk_operations_service)],
) -> BulkOperationResponse:
    """Create and execute a bulk operation on multiple devices."""
    logger.info(
        f"POST /bulk-operations - Creating bulk operation: {operation_request.operation_type} for {len(operation_request.targets)} devices"
    )
    _check_bulk_operations_feature_enabled(request)

    try:
        # Generate unique operation ID
        operation_id = f"op_{uuid.uuid4().hex[:12]}"

        # Create the bulk operation
        result = await bulk_service.create_operation(
            operation_id=operation_id,
            operation_type=operation_request.operation_type,
            targets=operation_request.targets,
            payload=operation_request.payload.model_dump(),
            description=operation_request.description,
        )

        logger.info(
            f"Bulk operation created: {operation_id} targeting {len(operation_request.targets)} devices"
        )
        return BulkOperationResponse(
            status=result["status"],
            operation_id=operation_id,
            total_tasks=len(operation_request.targets),
            queued_at=datetime.utcnow(),
        )

    except Exception as e:
        logger.error(f"Error creating bulk operation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create bulk operation") from e


@router.get(
    "/{operation_id}",
    response_model=dict[str, Any],
    summary="Get bulk operation status",
    description="Get the status and progress of a bulk operation.",
)
async def get_bulk_operation_status(
    request: Request,
    operation_id: str,
    bulk_service: Annotated[Any, Depends(get_bulk_operations_service)],
) -> dict[str, Any]:
    """Get the status and progress of a bulk operation."""
    logger.debug(f"GET /bulk-operations/{operation_id} - Retrieving operation status")
    _check_bulk_operations_feature_enabled(request)

    try:
        status = await bulk_service.get_operation_status(operation_id)
        if not status:
            raise HTTPException(status_code=404, detail="Operation not found")

        return status

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving operation status for {operation_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve operation status") from e


# Device Groups endpoints
@router.get(
    "/groups",
    response_model=list[DeviceGroup],
    summary="List device groups",
    description="Get all user-defined device groups.",
)
async def list_device_groups(
    request: Request,
    bulk_service: Annotated[Any, Depends(get_bulk_operations_service)],
) -> list[DeviceGroup]:
    """Get all user-defined device groups."""
    logger.debug("GET /bulk-operations/groups - Retrieving device groups")
    _check_bulk_operations_feature_enabled(request)

    try:
        groups = await bulk_service.list_groups()
        return groups

    except Exception as e:
        logger.error(f"Error retrieving device groups: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve device groups") from e


@router.post(
    "/groups",
    response_model=DeviceGroup,
    summary="Create device group",
    description="Create a new device group for bulk operations.",
)
async def create_device_group(
    request: Request,
    group_request: DeviceGroupRequest,
    bulk_service: Annotated[Any, Depends(get_bulk_operations_service)],
) -> DeviceGroup:
    """Create a new device group."""
    logger.info(
        f"POST /bulk-operations/groups - Creating group: {group_request.name} with {len(group_request.device_ids)} devices"
    )
    _check_bulk_operations_feature_enabled(request)

    try:
        group_id = f"grp_{uuid.uuid4().hex[:12]}"

        group = await bulk_service.create_group(
            group_id=group_id,
            name=group_request.name,
            description=group_request.description,
            device_ids=group_request.device_ids,
            exemptions=group_request.exemptions,
        )

        logger.info(f"Device group created: {group_id} - {group_request.name}")
        return group

    except Exception as e:
        logger.error(f"Error creating device group: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create device group") from e


@router.put(
    "/groups/{group_id}",
    response_model=DeviceGroup,
    summary="Update device group",
    description="Update an existing device group.",
)
async def update_device_group(
    request: Request,
    group_id: str,
    group_request: DeviceGroupRequest,
    bulk_service: Annotated[Any, Depends(get_bulk_operations_service)],
) -> DeviceGroup:
    """Update an existing device group."""
    logger.info(f"PUT /bulk-operations/groups/{group_id} - Updating group: {group_request.name}")
    _check_bulk_operations_feature_enabled(request)

    try:
        group = await bulk_service.update_group(
            group_id=group_id,
            name=group_request.name,
            description=group_request.description,
            device_ids=group_request.device_ids,
            exemptions=group_request.exemptions,
        )

        if not group:
            raise HTTPException(status_code=404, detail="Group not found")

        logger.info(f"Device group updated: {group_id}")
        return group

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating device group {group_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to update device group") from e


@router.delete(
    "/groups/{group_id}",
    summary="Delete device group",
    description="Delete a device group.",
)
async def delete_device_group(
    request: Request,
    group_id: str,
    bulk_service: Annotated[Any, Depends(get_bulk_operations_service)],
) -> dict[str, str]:
    """Delete a device group."""
    logger.info(f"DELETE /bulk-operations/groups/{group_id} - Deleting group")
    _check_bulk_operations_feature_enabled(request)

    try:
        success = await bulk_service.delete_group(group_id)
        if not success:
            raise HTTPException(status_code=404, detail="Group not found")

        logger.info(f"Device group deleted: {group_id}")
        return {"message": "Group deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting device group {group_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to delete device group") from e


@router.post(
    "/groups/{group_id}/execute",
    response_model=BulkOperationResponse,
    summary="Execute group operation",
    description="Execute a bulk operation on all devices in a group.",
)
async def execute_group_operation(
    request: Request,
    group_id: str,
    payload: BulkOperationPayload,
    bulk_service: Annotated[Any, Depends(get_bulk_operations_service)],
) -> BulkOperationResponse:
    """Execute a bulk operation on all devices in a group."""
    logger.info(f"POST /bulk-operations/groups/{group_id}/execute - Executing group operation")
    _check_bulk_operations_feature_enabled(request)

    try:
        # Get the group to find device IDs
        groups = await bulk_service.list_groups()
        group = next((g for g in groups if g.id == group_id), None)

        if not group:
            raise HTTPException(status_code=404, detail="Group not found")

        # Create bulk operation for the group
        operation_id = f"op_{uuid.uuid4().hex[:12]}_grp"

        result = await bulk_service.create_operation(
            operation_id=operation_id,
            operation_type="group_operation",
            targets=group.device_ids,
            payload=payload.model_dump(),
            description=f"Group operation: {group.name}",
        )

        logger.info(f"Group operation created: {operation_id} for group {group.name}")
        return BulkOperationResponse(
            status=result["status"],
            operation_id=operation_id,
            total_tasks=len(group.device_ids),
            queued_at=datetime.utcnow(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing group operation for {group_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to execute group operation") from e
