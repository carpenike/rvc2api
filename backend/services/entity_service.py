"""
Entity Service

Handles business logic for RV-C entity management, including:
- Entity querying and filtering
- Entity state management
- Light control with CAN command sending
- History management
- Metadata extraction

This service uses the EntityManagerFeature for unified entity management,
completely removing legacy state dictionary dependencies.
"""

import logging
import time
from typing import Any

from backend.core.entity_manager import EntityManager
from backend.integrations.can.manager import can_tx_queue
from backend.integrations.can.message_factory import create_light_can_message
from backend.models.entity import ControlCommand, ControlEntityResponse
from backend.models.unmapped import UnknownPGNEntry, UnmappedEntryModel
from backend.websocket.handlers import WebSocketManager

logger = logging.getLogger(__name__)


class EntityService:
    """
    Service for managing RV-C entities and their control operations.

    This service provides business logic for entity operations using the
    EntityManagerFeature for unified entity management, completely removing
    legacy state dictionary dependencies.
    """

    def __init__(
        self,
        websocket_manager: WebSocketManager,
        entity_manager: EntityManager | None = None,
    ):
        """
        Initialize the entity service.

        Args:
            websocket_manager: WebSocket communication manager
            entity_manager: EntityManager instance (will be retrieved from feature manager if None)
        """
        self.websocket_manager = websocket_manager
        self._entity_manager = entity_manager

    @property
    def entity_manager(self) -> EntityManager:
        """Get the EntityManager instance."""
        if self._entity_manager is None:
            # Get entity manager from feature manager
            from backend.services.feature_manager import get_feature_manager

            feature_manager = get_feature_manager()
            entity_manager_feature = feature_manager.get_feature("entity_manager")
            if entity_manager_feature is None:
                raise RuntimeError("EntityManager feature not found in feature manager")

            self._entity_manager = entity_manager_feature.get_entity_manager()

        return self._entity_manager

    async def list_entities(
        self,
        device_type: str | None = None,
        area: str | None = None,
    ) -> dict[str, dict[str, Any]]:
        """
        List all entities with optional filtering.

        Args:
            device_type: Optional filter by entity device_type
            area: Optional filter by entity suggested_area

        Returns:
            Dictionary of entities matching the filter criteria
        """
        # Use EntityManager for efficient filtering
        filtered_entities = self.entity_manager.filter_entities(device_type=device_type, area=area)
        # Convert to API format
        return {entity_id: entity.to_dict() for entity_id, entity in filtered_entities.items()}

    async def list_entity_ids(self) -> list[str]:
        """Return all known entity IDs."""
        return self.entity_manager.get_entity_ids()

    async def get_entity(self, entity_id: str) -> dict[str, Any] | None:
        """
        Get a specific entity by ID.

        Args:
            entity_id: The ID of the entity to retrieve

        Returns:
            The entity data or None if not found
        """
        entity = self.entity_manager.get_entity(entity_id)
        if entity:
            return entity.to_dict()
        return None

    async def get_entity_history(
        self,
        entity_id: str,
        since: float | None = None,
        limit: int | None = 1000,
    ) -> list[dict[str, Any]] | None:
        """
        Get entity history with optional filtering.

        Args:
            entity_id: The ID of the entity
            since: Optional Unix timestamp to filter entries newer than this
            limit: Optional limit on the number of points to return

        Returns:
            List of entity history entries or None if entity not found
        """
        entity = self.entity_manager.get_entity(entity_id)
        if entity:
            # Get history from the entity with optional filtering
            history_entries = entity.get_history(count=limit, since=since)
            # Convert each EntityState to a dictionary
            return [state.model_dump() for state in history_entries]
        return None

    async def get_unmapped_entries(self) -> dict[str, UnmappedEntryModel]:
        """
        Get unmapped entries.

        Returns:
            Dictionary of unmapped entries
        """
        # Use EntityManager for unmapped entries
        return {
            key: UnmappedEntryModel(**entry)
            for key, entry in self.entity_manager.unmapped_entries.items()
        }

    async def get_unknown_pgns(self) -> dict[str, UnknownPGNEntry]:
        """
        Get unknown PGN entries.

        Returns:
            Dictionary of unknown PGN entries
        """
        # Use EntityManager for unknown PGNs
        return {
            key: UnknownPGNEntry(**entry) for key, entry in self.entity_manager.unknown_pgns.items()
        }

    async def get_metadata(self) -> dict[str, list[str]]:
        """
        Get metadata about available entity attributes.

        Returns:
            Dictionary with lists of available values for each metadata category
        """
        # Define metadata categories
        metadata = {
            "device_types": [],
            "capabilities": [],
            "suggested_areas": [],
            "groups": [],
        }

        # Extract metadata from entity configurations using EntityManager
        entity_configs = {
            entity_id: entity.config
            for entity_id, entity in self.entity_manager.get_all_entities().items()
        }

        # Extract metadata from entity configurations
        for config in entity_configs.values():
            if device_type := config.get("device_type"):
                metadata["device_types"].append(device_type)
            if capabilities := config.get("capabilities"):
                metadata["capabilities"].extend(capabilities)
            if suggested_area := config.get("suggested_area"):
                metadata["suggested_areas"].append(suggested_area)
            if groups := config.get("groups"):
                metadata["groups"].extend(groups)

        # Remove duplicates and sort
        for key in metadata:
            metadata[key] = sorted(set(metadata[key]))

        # Extract available commands from light capabilities
        command_set: set[str] = set()

        # Get light entities from EntityManager
        light_entities = self.entity_manager.filter_entities(device_type="light")

        for _entity_id, entity in light_entities.items():
            caps = entity.config.get("capabilities", [])
            command_set.add("set")  # Always available for lights
            if "dimmable" in caps:
                command_set.add("brightness_up")
                command_set.add("brightness_down")

        metadata["available_commands"] = sorted(command_set)

        return metadata

    async def control_light(self, entity_id: str, cmd: ControlCommand) -> ControlEntityResponse:
        """
        Control a light entity.

        Args:
            entity_id: The ID of the light entity to control
            cmd: Control command with action details

        Returns:
            Response with success status and action description

        Raises:
            ValueError: If entity not found or command invalid
            RuntimeError: If CAN command fails to send
        """
        # Validate entity exists
        entity = self.entity_manager.get_entity(entity_id)
        if not entity:
            raise ValueError(f"Entity '{entity_id}' not found")

        if entity.config.get("device_type") != "light":
            raise ValueError(f"Entity '{entity_id}' is not controllable as a light")

        # Get current state and brightness information
        current_state = entity.get_state()
        current_state_data = current_state.model_dump()
        current_raw_values = current_state_data.get("raw", {})
        current_brightness_raw = current_raw_values.get("operating_status", 0)
        current_brightness_ui = int((current_brightness_raw / 200.0) * 100)
        current_on_str = current_state_data.get("state", "off")
        current_on = current_on_str.lower() == "on"

        # Convert CAN brightness to UI brightness (0-100)
        target_brightness_ui = cmd.brightness or 100
        action = ""

        if cmd.command == "set":
            if cmd.state == "on":
                # If no brightness specified, use last known or default to 100%
                if cmd.brightness is None:
                    last_brightness_ui = getattr(entity, "last_known_brightness", 100)
                    target_brightness_ui = last_brightness_ui
                action = f"Set ON to {target_brightness_ui}%"
                # Store last known brightness
                entity.last_known_brightness = target_brightness_ui
            elif cmd.state == "off":
                target_brightness_ui = 0
                # Store current brightness as last known if light is currently on
                if current_on and current_brightness_ui > 0:
                    entity.last_known_brightness = current_brightness_ui
                action = "Set OFF"
        elif cmd.command == "toggle":
            if current_on:
                target_brightness_ui = 0
                # Store current brightness as last known
                if current_brightness_ui > 0:
                    entity.last_known_brightness = current_brightness_ui
                action = "Toggle OFF"
            else:
                # Use last known brightness or default to 100%
                last_brightness_ui = getattr(entity, "last_known_brightness", 100)
                target_brightness_ui = last_brightness_ui
                action = f"Toggle ON to {target_brightness_ui}%"
        elif cmd.command in ["brightness_up", "brightness_down"]:
            step = 10  # 10% steps
            if cmd.command == "brightness_up":
                target_brightness_ui = min(100, current_brightness_ui + step)
            else:
                target_brightness_ui = max(0, current_brightness_ui - step)
            action = f"Adjust to {target_brightness_ui}%"
        else:
            raise ValueError(f"Invalid command: {cmd.command}")

        # Store brightness if light will be on
        if target_brightness_ui > 0:
            entity.last_known_brightness = target_brightness_ui

        return await self._execute_light_command(entity_id, target_brightness_ui, action)

    async def _execute_light_command(
        self,
        entity_id: str,
        target_brightness_ui: int,
        action_description: str,
    ) -> ControlEntityResponse:
        """
        Execute a light control command by sending CAN messages.

        Args:
            entity_id: The entity ID
            target_brightness_ui: Target brightness (0-100)
            action_description: Description of the action being taken

        Returns:
            Control response with status and details
        """
        # Get entity information for CAN message creation
        entity = self.entity_manager.get_entity(entity_id)
        if not entity:
            raise RuntimeError(
                f"Control Error: {entity_id} not found in entity manager for "
                f"action '{action_description}'"
            )

        # Extract info needed for CAN message creation from entity config
        entity_config = entity.config
        instance = entity_config.get("instance")
        if instance is None:
            raise RuntimeError(f"Entity {entity_id} missing 'instance' for CAN message creation")

        # Create optimistic update payload
        ts = time.time()
        optimistic_state_str = "on" if target_brightness_ui > 0 else "off"
        optimistic_raw_val = int((target_brightness_ui / 100.0) * 200)

        optimistic_payload = {
            "entity_id": entity_id,
            "timestamp": ts,
            "state": optimistic_state_str,
            "raw": optimistic_raw_val,
            "brightness_pct": target_brightness_ui,
            "suggested_area": entity_config.get("suggested_area", "unknown"),
            "device_type": entity_config.get("device_type", "unknown"),
            "capabilities": entity_config.get("capabilities", []),
            "friendly_name": entity_config.get("friendly_name", entity_id),
            "groups": entity_config.get("groups", []),
        }

        # Update entity state optimistically
        entity.update_state(optimistic_payload)

        # Broadcast update via WebSocket
        broadcast_data = {"entity_id": entity_id, "data": optimistic_payload}
        await self.websocket_manager.broadcast_to_data_clients(broadcast_data)

        # Create and send CAN message
        try:
            decoded = None
            can_message = create_light_can_message(
                pgn=0x1F0D0,  # Standard PGN for DML_COMMAND_2 light commands
                instance=instance,
                brightness_can_level=optimistic_raw_val,
            )
            await can_tx_queue.put((can_message, "vcan0"))  # TODO: Make interface configurable

            # Add sniffer entry for TX tracking
            sniffer_entry = {
                "timestamp": ts,
                "interface": "vcan0",  # TODO: Make configurable
                "can_id": f"{can_message.arbitration_id:08X}",
                "data": can_message.data.hex().upper(),
                "dlc": len(can_message.data),
                "is_extended": can_message.is_extended_id,
                "decoded": decoded,
                "origin": "self",
            }
            logger.debug(f"Adding TX sniffer entry: {sniffer_entry}")

            # Note: Since we removed AppState dependency, we don't track pending commands
            # This could be added to EntityManager or handled differently if needed
            logger.debug("Successfully sent CAN command")

            # Broadcast the state update via WebSocket
            await self.websocket_manager.broadcast_to_data_clients(
                {
                    "type": "entity_update",
                    "entity_id": entity_id,
                    "state": optimistic_state_str,
                    "brightness": target_brightness_ui,
                    "timestamp": ts,
                }
            )

            return ControlEntityResponse(
                status="success",
                entity_id=entity_id,
                command=action_description,
                state=optimistic_state_str,
                brightness=target_brightness_ui,
                action=action_description,
            )
        except Exception as e:
            logger.error(f"CAN command failed for {entity_id}: {e}")
            raise RuntimeError(f"CAN command failed: {e}") from e
