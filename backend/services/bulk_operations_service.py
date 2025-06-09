"""
Bulk Operations Service

Handles bulk device operations with asynchronous processing and WebSocket progress updates.
Implements transactional model for reliable multi-device operations.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any

from backend.core.dependencies import get_entity_service
from backend.models.bulk_operations import BulkOperationModel, DeviceGroupModel
from backend.services.in_memory_persistence import InMemoryPersistenceService

logger = logging.getLogger(__name__)


class BulkOperationsService:
    """
    Service for managing bulk operations and device groups.

    Implements asynchronous job processing with granular progress tracking
    and WebSocket notifications for real-time updates.
    """

    def __init__(self, entity_service: Any = None, websocket_manager: Any = None):
        """
        Initialize the bulk operations service.

        Args:
            entity_service: Entity service for device operations
            websocket_manager: WebSocket manager for progress updates
        """
        self.entity_service = entity_service or get_entity_service()
        self.websocket_manager = websocket_manager
        self.persistence = InMemoryPersistenceService()

        # In-memory storage for operations and groups
        self.operations: dict[str, BulkOperationModel] = {}
        self.groups: dict[str, DeviceGroupModel] = {}

        logger.info("BulkOperationsService initialized")

    async def create_operation(
        self,
        operation_id: str,
        operation_type: str,
        targets: list[str],
        payload: dict[str, Any],
        description: str | None = None,
    ) -> dict[str, Any]:
        """
        Create and start a bulk operation.

        Args:
            operation_id: Unique operation identifier
            operation_type: Type of operation (state_change, configuration_change, etc.)
            targets: List of device IDs to target
            payload: Operation payload with command and parameters
            description: Human-readable description

        Returns:
            Operation creation result
        """
        logger.info(
            f"Creating bulk operation {operation_id}: {operation_type} for {len(targets)} devices"
        )

        # Create operation model
        operation = BulkOperationModel(
            id=operation_id,
            operation_type=operation_type,
            targets=targets,
            payload=payload,
            description=description,
            status="QUEUED",
            total_tasks=len(targets),
            success_count=0,
            failure_count=0,
            failed_devices=[],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Store operation
        self.operations[operation_id] = operation

        # Start async processing
        task = asyncio.create_task(self._process_operation(operation_id))
        # Store task reference to prevent garbage collection
        operation.task = task

        return {
            "status": "QUEUED",
            "operation_id": operation_id,
            "message": f"Bulk operation queued for {len(targets)} devices",
        }

    async def get_operation_status(self, operation_id: str) -> dict[str, Any] | None:
        """
        Get the status of a bulk operation.

        Args:
            operation_id: Operation identifier

        Returns:
            Operation status information or None if not found
        """
        operation = self.operations.get(operation_id)
        if not operation:
            return None

        return {
            "operation_id": operation.id,
            "status": operation.status,
            "operation_type": operation.operation_type,
            "description": operation.description,
            "total_tasks": operation.total_tasks,
            "success_count": operation.success_count,
            "failure_count": operation.failure_count,
            "progress_percentage": round(
                (operation.success_count + operation.failure_count) / operation.total_tasks * 100,
                1,
            ),
            "failed_devices": operation.failed_devices,
            "created_at": operation.created_at.isoformat(),
            "updated_at": operation.updated_at.isoformat(),
        }

    async def _process_operation(self, operation_id: str) -> None:
        """
        Process a bulk operation asynchronously.

        Args:
            operation_id: Operation to process
        """
        operation = self.operations.get(operation_id)
        if not operation:
            logger.error(f"Operation {operation_id} not found for processing")
            return

        logger.info(f"Starting processing of operation {operation_id}")
        operation.status = "PROCESSING"
        operation.updated_at = datetime.utcnow()

        try:
            for device_id in operation.targets:
                try:
                    # Process individual device with rate limiting
                    await self._process_device_operation(operation, device_id)

                    # Rate limiting to prevent RV-C bus flooding (100ms between commands)
                    await asyncio.sleep(0.1)

                except Exception as e:
                    logger.error(
                        f"Error processing device {device_id} in operation {operation_id}: {e}"
                    )
                    operation.failure_count += 1
                    operation.failed_devices.append(
                        {
                            "device_id": device_id,
                            "error": str(e),
                            "timestamp": datetime.utcnow().isoformat(),
                        }
                    )

                    # Send device failure WebSocket event
                    await self._send_progress_update(operation_id, device_id, "FAILED", str(e))

            # Determine final status
            if operation.failure_count == 0:
                operation.status = "COMPLETED"
            elif operation.success_count == 0:
                operation.status = "FAILED"
            else:
                operation.status = "PARTIAL_SUCCESS"

            operation.updated_at = datetime.utcnow()

            # Send completion WebSocket event
            await self._send_completion_update(operation)

            logger.info(
                f"Operation {operation_id} completed: {operation.success_count} succeeded, {operation.failure_count} failed"
            )

        except Exception as e:
            logger.error(
                f"Critical error processing operation {operation_id}: {e}",
                exc_info=True,
            )
            operation.status = "FAILED"
            operation.updated_at = datetime.utcnow()

    async def _process_device_operation(
        self, operation: BulkOperationModel, device_id: str
    ) -> None:
        """
        Process operation for a single device.

        Args:
            operation: Bulk operation context
            device_id: Device to process
        """
        try:
            payload = operation.payload
            command = payload.get("command")

            if operation.operation_type == "state_change":
                # Handle state change operations (on/off, brightness)
                if command == "set":
                    state = payload.get("state")
                    brightness = payload.get("brightness")

                    # Use existing entity service command structure
                    entity_command = {"command": "set"}
                    if state:
                        entity_command["state"] = state
                    if brightness is not None:
                        entity_command["brightness"] = brightness

                    # Execute command via entity service
                    await self.entity_service.control_entity(device_id, entity_command)

                elif command in ["toggle", "brightness_up", "brightness_down"]:
                    # Direct commands
                    await self.entity_service.control_entity(device_id, {"command": command})

            elif operation.operation_type == "status_check":
                # Request status update
                await self.entity_service.request_entity_status(device_id)

            elif operation.operation_type == "configuration_change":
                # Handle configuration changes
                config_command = {
                    "command": command,
                    **{k: v for k, v in payload.items() if k != "command"},
                }
                await self.entity_service.configure_entity(device_id, config_command)

            # Success
            operation.success_count += 1
            await self._send_progress_update(operation.id, device_id, "SUCCESS")

        except Exception as e:
            # Error will be handled by caller
            raise e

    async def _send_progress_update(
        self,
        operation_id: str,
        device_id: str,
        status: str,
        error: str | None = None,
    ) -> None:
        """
        Send WebSocket progress update for a device.

        Args:
            operation_id: Operation identifier
            device_id: Device identifier
            status: Device operation status
            error: Error message if failed
        """
        if not self.websocket_manager:
            return

        event = {
            "event": "bulk_op_progress",
            "operation_id": operation_id,
            "device_id": device_id,
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if error:
            event["error"] = error

        try:
            await self.websocket_manager.broadcast(event)
        except Exception as e:
            logger.error(f"Error sending progress update: {e}")

    async def _send_completion_update(self, operation: BulkOperationModel) -> None:
        """
        Send WebSocket completion update for an operation.

        Args:
            operation: Completed operation
        """
        if not self.websocket_manager:
            return

        event = {
            "event": "bulk_op_complete",
            "operation_id": operation.id,
            "status": operation.status,
            "success_count": operation.success_count,
            "failure_count": operation.failure_count,
            "failed_devices": operation.failed_devices,
            "timestamp": operation.updated_at.isoformat(),
        }

        try:
            await self.websocket_manager.broadcast(event)
        except Exception as e:
            logger.error(f"Error sending completion update: {e}")

    # Device Groups Management
    async def list_groups(self) -> list[dict[str, Any]]:
        """Get all device groups."""
        return [group.to_dict() for group in self.groups.values()]

    async def create_group(
        self,
        group_id: str,
        name: str,
        device_ids: list[str],
        description: str | None = None,
        exemptions: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Create a new device group.

        Args:
            group_id: Unique group identifier
            name: Group name
            device_ids: List of device IDs
            description: Optional description
            exemptions: Optional exemptions for specific operations

        Returns:
            Created group data
        """
        group = DeviceGroupModel(
            id=group_id,
            name=name,
            description=description,
            device_ids=device_ids,
            exemptions=exemptions or {},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        self.groups[group_id] = group
        logger.info(f"Created device group: {group_id} - {name}")

        return group.to_dict()

    async def update_group(
        self,
        group_id: str,
        name: str,
        device_ids: list[str],
        description: str | None = None,
        exemptions: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Update an existing device group."""
        group = self.groups.get(group_id)
        if not group:
            return None

        group.name = name
        group.description = description
        group.device_ids = device_ids
        group.exemptions = exemptions or {}
        group.updated_at = datetime.utcnow()

        logger.info(f"Updated device group: {group_id}")
        return group.to_dict()

    async def delete_group(self, group_id: str) -> bool:
        """Delete a device group."""
        if group_id in self.groups:
            del self.groups[group_id]
            logger.info(f"Deleted device group: {group_id}")
            return True
        return False
