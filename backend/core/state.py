"""
AppState module: Maintains in-memory state, history, and configuration lookups for all entities.

This module defines the AppState class, which is responsible for managing the shared application state
across all entities, including their latest values, historical data, and configuration-derived lookups.
It is a core feature of the backend, supporting initialization, updates, and access patterns for entity state.
"""

import asyncio
import contextlib
import logging
import time
from collections import deque
from typing import Any

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
        )
        self.controller_source_addr: int = controller_source_addr
        self.state: dict[str, dict[str, Any]] = {}
        self.history_duration: int = 24 * 3600  # seconds
        self.max_history_length: int = 1000
        self.history: dict[str, deque[dict[str, Any]]] = {}
        self.unmapped_entries: dict[str, Any] = {}
        self.unknown_pgns: dict[str, Any] = {}
        self.last_known_brightness_levels: dict[str, int] = {}
        self.config_data: dict[str, Any] = config or {}
        self.background_tasks: set[Any] = set()
        self.pending_commands: list[Any] = []
        self.observed_source_addresses: set[Any] = set()
        self.known_command_status_pairs: dict[Any, Any] = {}
        self.can_sniffer_grouped: list[Any] = []
        self.last_seen_by_source_addr: dict[Any, Any] = {}
        self.can_command_sniffer_log: list[Any] = []
        self.entity_id_lookup: dict[Any, Any] = {}
        self.light_command_info: dict[Any, Any] = {}
        self.device_lookup: dict[Any, Any] = {}
        self.status_lookup: dict[Any, Any] = {}

    def __repr__(self) -> str:
        return (
            f"<AppState(state_keys={list(self.state.keys())}, "
            f"history_keys={list(self.history.keys())}, "
            f"unmapped_entries={len(self.unmapped_entries)}, "
            f"unknown_pgns={len(self.unknown_pgns)})>"
        )

    async def startup(self) -> None:
        """Initialize the state feature on startup."""
        logger.info("Starting AppState feature")

    async def shutdown(self) -> None:
        """Clean up resources on shutdown."""
        logger.info("Shutting down AppState feature")
        for task in self.background_tasks:
            task.cancel()

    @property
    def health(self) -> str:
        """Return the health status of the feature."""
        if not self.enabled:
            return "disabled"
        return "healthy"

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

    def initialize_app_from_config(self, config_data_tuple, decode_payload_function) -> None:
        """
        Initializes all configuration-derived application state.
        """
        (
            decoder_map_val,
            raw_device_mapping_val,
            device_lookup_val,
            status_lookup_val,
            light_entity_ids_set_val,
            entity_id_lookup_val,
            light_command_info_val,
            pgn_hex_to_name_map_val,
            dgn_pairs_val,
            coach_info_val,
        ) = config_data_tuple

        self.entity_id_lookup.clear()
        self.entity_id_lookup.update(entity_id_lookup_val)

        self.light_command_info.clear()
        self.light_command_info.update(light_command_info_val)

        self.device_lookup.clear()
        self.device_lookup.update(device_lookup_val)

        self.status_lookup.clear()
        self.status_lookup.update(status_lookup_val)

        self.decoder_map = decoder_map_val
        self.raw_device_mapping = raw_device_mapping_val
        self.pgn_hex_to_name_map = pgn_hex_to_name_map_val
        self.coach_info = coach_info_val

        self.light_entity_ids = sorted(light_entity_ids_set_val)

        if dgn_pairs_val:
            self.known_command_status_pairs.clear()
            for cmd_dgn, status_dgn in dgn_pairs_val.items():
                self.known_command_status_pairs[cmd_dgn.upper()] = status_dgn.upper()

        logger.info("Application state populated from configuration data.")

        self.initialize_history_deques()
        self.preseed_light_states(decode_payload_function)

        logger.info("Global app state dictionaries populated.")

    def get_last_known_brightness(self, entity_id) -> int:
        """
        Retrieves the last known brightness for a given light entity.
        """
        return self.last_known_brightness_levels.get(entity_id, 100)

    def set_last_known_brightness(self, entity_id, brightness) -> None:
        """
        Sets the last known brightness for a given light entity.
        """
        self.last_known_brightness_levels[entity_id] = brightness

    def initialize_history_deques(self) -> None:
        """Initializes the history dictionary with empty deques for each entity ID."""
        for eid in self.entity_id_lookup:
            if eid not in self.history:
                self.history[eid] = deque(maxlen=self.max_history_length)
        logger.info("History deques initialized for all entities.")

    def update_entity_state_and_history(self, entity_id, payload_to_store) -> None:
        """
        Updates the state and history for a given entity.
        """
        self.state[entity_id] = payload_to_store

        if entity_id in self.history:
            history_deque = self.history[entity_id]
            history_deque.append(payload_to_store)
            current_time = payload_to_store.get("timestamp", time.time())
            cutoff = current_time - self.history_duration
            while history_deque and history_deque[0]["timestamp"] < cutoff:
                history_deque.popleft()
        else:
            self.history[entity_id] = deque([payload_to_store], maxlen=self.max_history_length)
            logger.warning(f"History deque not found for {entity_id}, created new one.")

    def preseed_light_states(self, decode_payload_func) -> None:
        """
        Initializes the state and history for all known light entities to an "off" state.
        """
        now = time.time()
        logger.info(f"Pre-seeding states for {len(self.light_entity_ids)} light entities.")
        for eid in self.light_entity_ids:
            info = self.light_command_info.get(eid)
            entity_config = self.entity_id_lookup.get(eid)

            if not info or not entity_config:
                logger.warning(
                    f"Pre-seeding: Missing info or entity_config for light entity ID: {eid}"
                )
                continue

            dgn_for_status_hex_str = None
            raw_status_dgn_from_config = entity_config.get("status_dgn")

            if raw_status_dgn_from_config:
                dgn_for_status_hex_str = str(raw_status_dgn_from_config).upper().replace("0X", "")
            else:
                dgn_for_status_hex_str = format(info["dgn"], "X").upper()

            logger.debug(
                f"Pre-seeding {eid}: Using DGN {dgn_for_status_hex_str} for initial status."
            )

            spec_entry = None
            for entry_val in self.decoder_map.values():
                if entry_val.get("dgn_hex", "").upper().replace("0X", "") == dgn_for_status_hex_str:
                    spec_entry = entry_val
                    break

            if not spec_entry:
                logger.warning(
                    f"Pre-seeding: No spec entry found for DGN {dgn_for_status_hex_str} (entity: {eid})"
                )
                continue

            data_length = spec_entry.get("data_length", 8)
            initial_can_payload = bytes([0] * data_length)

            decoded, raw = decode_payload_func(spec_entry, initial_can_payload)

            brightness = raw.get("operating_status", 0)
            human_state = "on" if brightness > 0 else "off"

            payload = {
                "entity_id": eid,
                "value": decoded,
                "raw": raw,
                "state": human_state,
                "timestamp": now,
                "suggested_area": entity_config.get("suggested_area", "Unknown"),
                "device_type": entity_config.get("device_type", "light"),
                "capabilities": entity_config.get("capabilities", []),
                "friendly_name": entity_config.get("friendly_name"),
                "groups": entity_config.get("groups", []),
            }
            self.update_entity_state_and_history(eid, payload)
        logger.info("Finished pre-seeding light states.")

    def populate_app_state(
        self, rvc_spec_path=None, device_mapping_path=None, load_config_func=None
    ):
        """
        Populates the application state from configuration files.
        """
        if load_config_func is None:
            from rvc_decoder.decode import load_config_data

            load_config_func = load_config_data

        self.entity_id_lookup.clear()
        self.device_lookup.clear()
        self.status_lookup.clear()
        self.light_command_info.clear()
        self.state.clear()
        self.history.clear()
        self.unknown_pgns.clear()
        self.unmapped_entries.clear()
        self.last_known_brightness_levels.clear()

        logger.info("Cleared existing application state.")

        logger.info("Attempting to load and process device mapping...")
        processed_data_tuple = load_config_func(rvc_spec_path, device_mapping_path)

        (
            _decoder_map,
            _device_mapping_yaml,
            loaded_device_lookup,
            loaded_status_lookup,
            _light_entity_ids,
            loaded_entity_id_lookup,
            loaded_light_command_info,
            _pgn_hex_to_name_map,
            _dgn_pairs,
            _coach_info,
        ) = processed_data_tuple

        self.entity_id_lookup.update(loaded_entity_id_lookup)
        self.device_lookup.update(loaded_device_lookup)
        self.status_lookup.update(loaded_status_lookup)
        self.light_command_info.update(loaded_light_command_info)

        logger.info(
            f"After loading: app_state.entity_id_lookup has {len(self.entity_id_lookup)} entries."
        )
        logger.info(
            f"After loading: app_state.light_command_info has {len(self.light_command_info)} entries."
        )

        for eid in self.entity_id_lookup:
            if eid not in self.history:
                self.history[eid] = deque(maxlen=self.max_history_length)
        logger.info("History deques initialized for all entities.")

        self.initialize_app_from_config(
            processed_data_tuple, lambda *args: ({"operating_status": "0"}, {"operating_status": 0})
        )

    def notify_network_map_ws(self) -> None:
        """Notifies WebSocket clients about network map updates."""
        with contextlib.suppress(Exception):
            logger.debug("Network map update notification requested")
            # TODO: Implement network map WebSocket notification logic here
            pass

    def get_controller_source_addr(self) -> int:
        """Returns the controller's source address."""
        return self.controller_source_addr


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
        return app_state.state
    return {}


def get_history() -> dict:
    """Get the entity history dictionary."""
    if app_state:
        return app_state.history
    return {}


def get_entity_by_id(entity_id) -> dict | None:
    """
    Get an entity by its ID.
    """
    if app_state and entity_id in app_state.state:
        return app_state.state[entity_id]
    return None


def get_entity_history(entity_id, count=None) -> list:
    """
    Get historical data for an entity.
    """
    if not app_state or entity_id not in app_state.history:
        return []

    history_data = list(app_state.history[entity_id])
    if count is not None:
        return history_data[-count:]
    return history_data
