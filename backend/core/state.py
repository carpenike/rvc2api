"""
AppState module: Maintains in-memory state, history, and configuration lookups for all entities.

This module defines the AppState class, which is responsible for managing the shared application state
across all entities, including their latest values, historical data, and configuration-derived lookups.
It is a core feature of the backend, supporting initialization, updates, and access patterns for entity state.
"""

import asyncio
import contextlib
import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from backend.models.common import CoachInfo
    from backend.models.entity_model import EntityConfig

from backend.core.entity_manager import EntityManager
from backend.services.feature_base import Feature

logger = logging.getLogger(__name__)


class AppState(Feature):
    """
    Core feature that manages application state.

    Maintains the in-memory state of all entities, their historical data, and configuration-derived lookups.
    Provides methods to initialize, update, and access this shared state.
    """

    def __init__(
        self,
        name: str = "app_state",
        enabled: bool = True,
        core: bool = True,
        config: dict[str, Any] | None = None,
        dependencies: list[str] | None = None,
        controller_source_addr: int = 0xF9,
        friendly_name: str | None = None,
        safety_classification=None,
        log_state_transitions: bool = True,
        **kwargs
    ) -> None:
        """
        Initialize the AppState feature.
        """
        super().__init__(
            name=name,
            enabled=enabled,
            core=core,
            config=config or {},
            dependencies=dependencies or [],
            friendly_name=friendly_name,
            safety_classification=safety_classification,
            log_state_transitions=log_state_transitions,
        )
        self.controller_source_addr: int = controller_source_addr

        # Entity manager for unified entity state management
        self.entity_manager = EntityManager()

        # Configuration and mapping data
        self.raw_device_mapping: dict[tuple[str, str], dict[str, Any]] = {}
        self.pgn_hex_to_name_map: dict[str, str] = {}
        self.coach_info: CoachInfo | None = None
        self.max_history_length: int = 1000
        self.history_duration: int = 24 * 3600  # 24 hours in seconds

        # Non-entity state (these are not duplicated in EntityManager)
        self.unmapped_entries: dict[str, Any] = {}
        self.unknown_pgns: dict[str, Any] = {}
        self.config_data: dict[str, Any] = config or {}
        self.background_tasks: set[Any] = set()
        self.pending_commands: list[Any] = []
        self.observed_source_addresses: set[Any] = set()
        self.known_command_status_pairs: dict[Any, Any] = {}
        self.can_sniffer_grouped: list[Any] = []
        self.last_seen_by_source_addr: dict[Any, Any] = {}
        self.can_command_sniffer_log: list[Any] = []

    def __repr__(self) -> str:
        return (
            f"<AppState(entities={len(self.entity_manager.get_entity_ids())}, "
            f"light_entities={len(self.entity_manager.get_light_entity_ids())}, "
            f"unmapped_entries={len(self.unmapped_entries)}, "
            f"unknown_pgns={len(self.unknown_pgns)})>"
        )

    async def startup(self) -> None:
        """Initialize the state feature on startup."""
        global app_state
        app_state = self
        logger.info("Starting AppState feature")

        # Load entities from coach mapping file, similar to legacy system
        try:
            logger.info("Loading entity configuration from coach mapping files...")

            # Get configuration paths from settings
            from backend.core.config import get_settings

            settings = get_settings()

            rvc_spec_path = str(settings.rvc_spec_path) if settings.rvc_spec_path else None
            device_mapping_path = (
                str(settings.rvc_coach_mapping_path) if settings.rvc_coach_mapping_path else None
            )

            logger.info(f"Using RV-C spec path: {rvc_spec_path}")
            logger.info(f"Using device mapping path: {device_mapping_path}")

            self.populate_app_state(
                rvc_spec_path=rvc_spec_path, device_mapping_path=device_mapping_path
            )
            logger.info(f"Successfully loaded {len(self.entity_manager.get_entity_ids())} entities")
        except Exception as e:
            logger.error(f"Failed to load entity configuration during startup: {e}")
            # Don't fail startup completely, but log the error

    async def shutdown(self) -> None:
        """Clean up resources on shutdown."""
        logger.info("Shutting down AppState feature")
        for task in self.background_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                logger.debug("Background task cancelled successfully")
            except Exception as e:
                logger.error(f"Error during background task cancellation: {e}")
        self.background_tasks.clear()

    @property
    def health(self) -> str:
        """Return the health status of the feature."""
        return "healthy"  # State manager always healthy

    def set_broadcast_function(self, broadcast_func) -> None:
        """
        Set the function to broadcast CAN sniffer groups.
        """
        self._broadcast_can_sniffer_group = broadcast_func

    def get_observed_source_addresses(self) -> list[int]:
        """Returns a sorted list of all observed CAN source addresses."""
        return sorted(self.observed_source_addresses)

    def add_pending_command(self, entry) -> None:
        """
        Add a pending command and clean up old entries.
        """
        self.pending_commands.append(entry)
        now = entry["timestamp"]
        new_pending = []
        for cmd in self.pending_commands:
            if now - cmd["timestamp"] < 2.0:
                new_pending.append(cmd)
        self.pending_commands[:] = new_pending

    def try_group_response(self, response_entry) -> bool:
        """
        Try to group a response (RX) with a pending command (TX).
        """
        now = response_entry["timestamp"]
        instance = response_entry.get("instance")
        dgn = response_entry.get("dgn_hex")

        for cmd in self.pending_commands:
            cmd_dgn = cmd.get("dgn_hex")
            if (
                cmd.get("instance") == instance
                and isinstance(cmd_dgn, str)
                and self.known_command_status_pairs.get(cmd_dgn) == dgn
                and 0 <= now - cmd["timestamp"] < 1.0
            ):
                group = {
                    "command": cmd,
                    "response": response_entry,
                    "confidence": "high",
                    "reason": "mapping",
                }
                self.can_sniffer_grouped.append(group)
                # Limit grouped entries to prevent memory buildup (keep last 500 groups)
                if len(self.can_sniffer_grouped) > 500:
                    self.can_sniffer_grouped.pop(0)
                if self._broadcast_can_sniffer_group:
                    task = asyncio.create_task(self._broadcast_can_sniffer_group(group))
                    self.background_tasks.add(task)
                    task.add_done_callback(self.background_tasks.discard)
                self.pending_commands.remove(cmd)
                return True

        for cmd in self.pending_commands:
            if cmd.get("instance") == instance and 0 <= now - cmd["timestamp"] < 0.5:
                group = {
                    "command": cmd,
                    "response": response_entry,
                    "confidence": "low",
                    "reason": "heuristic",
                }
                self.can_sniffer_grouped.append(group)
                # Limit grouped entries to prevent memory buildup (keep last 500 groups)
                if len(self.can_sniffer_grouped) > 500:
                    self.can_sniffer_grouped.pop(0)
                if self._broadcast_can_sniffer_group:
                    task = asyncio.create_task(self._broadcast_can_sniffer_group(group))
                    self.background_tasks.add(task)
                    task.add_done_callback(self.background_tasks.discard)
                self.pending_commands.remove(cmd)
                return True
        return False

    def get_can_sniffer_grouped(self) -> list:
        """Returns the list of grouped CAN sniffer entries."""
        return list(self.can_sniffer_grouped)

    def update_last_seen_by_source_addr(self, entry) -> None:
        """
        Update the mapping of source address to the last-seen CAN sniffer entry.
        """
        src = entry.get("source_addr")
        if src is not None:
            self.last_seen_by_source_addr[src] = entry
            self.observed_source_addresses.add(src)

    def add_can_sniffer_entry(self, entry) -> None:
        """
        Adds a CAN command/control message entry to the sniffer log.
        """
        self.can_command_sniffer_log.append(entry)
        self.update_last_seen_by_source_addr(entry)
        if len(self.can_command_sniffer_log) > 1000:
            self.can_command_sniffer_log.pop(0)
        self.notify_network_map_ws()

    def get_can_sniffer_log(self) -> list:
        """Returns the current CAN command/control sniffer log."""
        return list(self.can_command_sniffer_log)

    def get_last_known_brightness(self, entity_id) -> int:
        """
        Retrieves the last known brightness for a given light entity.
        """
        entity = self.entity_manager.get_entity(entity_id)
        if entity and entity.last_known_brightness is not None:
            return entity.last_known_brightness
        return 100  # Default brightness

    def set_last_known_brightness(self, entity_id, brightness) -> None:
        """
        Sets the last known brightness for a given light entity.
        """
        entity = self.entity_manager.get_entity(entity_id)
        if entity:
            entity.last_known_brightness = brightness

    def update_entity_state_and_history(self, entity_id, payload_to_store) -> None:
        """
        Updates the state and history for a given entity using the EntityManager.
        """
        # Update the entity in the EntityManager (this handles both state and history)
        entity = self.entity_manager.get_entity(entity_id)
        if entity:
            entity.update_state(payload_to_store)
        else:
            # If entity doesn't exist in the EntityManager, try to register it
            # This can happen during runtime when new entities are discovered
            from backend.models.entity_model import EntityConfig

            # Create a minimal config from the payload
            config = EntityConfig(
                device_type=payload_to_store.get("device_type", "unknown"),
                suggested_area=payload_to_store.get("suggested_area", "Unknown"),
                friendly_name=payload_to_store.get("friendly_name"),
                capabilities=payload_to_store.get("capabilities", []),
                groups=payload_to_store.get("groups", []),
            )
            entity = self.entity_manager.register_entity(entity_id, config)
            entity.update_state(payload_to_store)

    def populate_app_state(
        self, rvc_spec_path=None, device_mapping_path=None, load_config_func=None
    ):
        """
        Populates the application state from configuration files.
        """
        logger.info(
            f"populate_app_state: rvc_spec_path={rvc_spec_path}, device_mapping_path={device_mapping_path}, load_config_func={load_config_func}"
        )
        logger.info("populate_app_state: Starting entity/config loading...")
        if load_config_func is None:
            from backend.integrations.rvc.decode import load_config_data

            load_config_func = load_config_data

        logger.info(f"populate_app_state: Using load_config_func={load_config_func}")

        # Clear previous state
        self.unknown_pgns.clear()
        self.unmapped_entries.clear()
        logger.info("populate_app_state: Cleared in-memory state.")

        try:
            processed_data_tuple = load_config_func(rvc_spec_path, device_mapping_path)
        except Exception as e:
            logger.error(f"populate_app_state: load_config_func failed: {e}")
            raise

        (
            decoder_map_val,
            spec_meta_val,
            mapping_dict_val,
            entity_map_val,
            entity_ids_val,
            inst_map_val,
            unique_instances_val,
            pgn_hex_to_name_map_val,
            dgn_pairs_val,
            coach_info_val,
        ) = processed_data_tuple

        logger.info(f"populate_app_state: entity_map has {len(entity_map_val)} entries.")
        logger.info(f"populate_app_state: entity_ids has {len(entity_ids_val)} entries.")

        # Store configuration data
        self.raw_device_mapping = mapping_dict_val
        self.pgn_hex_to_name_map = pgn_hex_to_name_map_val
        self.coach_info = coach_info_val

        if dgn_pairs_val:
            self.known_command_status_pairs.clear()
            for cmd_dgn, status_dgn in dgn_pairs_val.items():
                # dgn_pairs_val contains command PGN -> status PGN string mappings from YAML
                # Store the mapping of command DGN to status DGN for legacy compatibility
                self.known_command_status_pairs[cmd_dgn.upper()] = status_dgn.upper()

        logger.info("Application state populated from configuration data.")

        # Build the correct entity ID to config mapping from entity_map
        # entity_map is keyed by (dgn_hex, instance) tuples, but EntityManager expects
        # entity configs keyed by entity_id strings
        entity_configs: dict[str, EntityConfig] = {}
        for entity_dict in entity_map_val.values():
            if isinstance(entity_dict, dict) and "entity_id" in entity_dict:
                entity_id = entity_dict["entity_id"]
                # Use the dictionary directly as it's already compatible with EntityConfig
                entity_configs[entity_id] = entity_dict

        logger.info(f"Built entity configs mapping with {len(entity_configs)} entities")

        # Count lights for verification
        light_count = sum(
            1
            for config in entity_configs.values()
            if isinstance(config, dict) and config.get("device_type") == "light"
        )
        logger.info(f"Found {light_count} light entities in entity configs")

        # Update the entity manager with loaded entities
        self.entity_manager.bulk_load_entities(entity_configs)

        # Initialize light states
        from backend.integrations.rvc.decode import decode_payload

        self.entity_manager.preseed_light_states(decode_payload, entity_map_val)

        logger.info("Global app state dictionaries populated.")

    def notify_network_map_ws(self) -> None:
        """Notifies WebSocket clients about network map updates."""
        with contextlib.suppress(Exception):
            logger.debug("Network map update notification requested")
            # TODO: Implement network map WebSocket notification logic here

    def get_controller_source_addr(self) -> int:
        """Returns the controller's source address."""
        return self.controller_source_addr

    def get_health_status(self) -> dict:
        """
        Return a mock health status for testing and API compatibility.
        """
        return {
            "status": "healthy",
            "components": {
                "entities": len(self.entity_manager.get_entity_ids()),
                "unmapped_entries": len(self.unmapped_entries),
                "unknown_pgns": len(self.unknown_pgns),
            },
        }

    def start_can_sniffer(self, interface_name: str) -> None:
        """Start the CAN sniffer on the given interface."""
        from backend.core.state import CANSniffer  # for test patching

        self.can_sniffer = CANSniffer(interface_name, self.process_message)
        self.can_sniffer.start()

    def stop_can_sniffer(self) -> None:
        """Stop the CAN sniffer if running."""
        if hasattr(self, "can_sniffer") and self.can_sniffer:
            self.can_sniffer.stop()
            self.can_sniffer = None

    def get_entity_count(self) -> int:
        """Return the number of tracked entity states."""
        return len(getattr(self, "_entity_states", {}))

    def add_entity_state(self, entity_id: str, entity_data: dict) -> None:
        """Add or set the state for an entity."""
        if not hasattr(self, "_entity_states"):
            self._entity_states = {}
        self._entity_states[entity_id] = entity_data.copy()

    def get_entity_state(self, entity_id: str) -> dict | None:
        """Get the state for an entity, or None if not found."""
        return getattr(self, "_entity_states", {}).get(entity_id)

    def update_entity_state(self, entity_id: str, update_data: dict) -> None:
        """Update the state for an entity, merging with existing data."""
        if not hasattr(self, "_entity_states"):
            self._entity_states = {}
        if entity_id in self._entity_states:
            self._entity_states[entity_id].update(update_data)
        else:
            self._entity_states[entity_id] = update_data.copy()

    def remove_entity_state(self, entity_id: str) -> None:
        """Remove the state for an entity if it exists."""
        if hasattr(self, "_entity_states"):
            self._entity_states.pop(entity_id, None)

    def get_all_entity_states(self) -> dict:
        """Return a copy of all entity states."""
        return dict(getattr(self, "_entity_states", {}))

    def clear_entity_states(self) -> None:
        """Remove all entity states."""
        if hasattr(self, "_entity_states"):
            self._entity_states.clear()

    def _decode_rvc_message(self, message):
        """Stub for test patching; decodes an RVC message."""
        return {}

    def process_message(self, message):
        """Process a CAN message, decoding and handling errors gracefully (for test compatibility)."""
        try:
            self._decode_rvc_message(message)
        except Exception as e:
            logger.error(f"Error decoding RVC message: {e}")


# Dummy CANSniffer for test patching
class CANSniffer:
    def __init__(self, *args, **kwargs):
        pass

    def start(self):
        pass

    def stop(self):
        pass


app_state = None


def initialize_app_state(manager, config) -> AppState:
    """
    Initialize the application state singleton.
    """
    global app_state

    if app_state is None:
        app_state = AppState(
            name="app_state",
            enabled=True,
            core=True,
            config=config,
            dependencies=[],
        )
        manager.register_feature(app_state)

    return app_state


def get_state() -> dict:
    """Get the current entity state dictionary."""
    if app_state:
        return app_state.entity_manager.to_api_response()
    return {}


def get_history() -> dict:
    """Get the entity history dictionary."""
    if app_state:
        history_dict = {}
        for entity_id, entity in app_state.entity_manager.get_all_entities().items():
            history_dict[entity_id] = [state.model_dump() for state in entity.get_history()]
        return history_dict
    return {}


def get_entity_by_id(entity_id) -> dict | None:
    """
    Get an entity by its ID.
    """
    if app_state:
        entity = app_state.entity_manager.get_entity(entity_id)
        if entity:
            return entity.to_dict()
    return None


def get_entity_history(entity_id, count=None) -> list:
    """
    Get historical data for an entity.
    """
    if not app_state:
        return []

    entity = app_state.entity_manager.get_entity(entity_id)
    if not entity:
        return []

    return [state.model_dump() for state in entity.get_history(count=count)]
