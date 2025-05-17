"""
Manages the in-memory application state for the rvc2api daemon.

This module holds the current state of all entities, their historical data,
and configuration-derived lookups (like entity definitions, light commands, etc.).
It provides functions to initialize, update, and access this shared state.
"""

import asyncio
import logging
import time
from collections import deque
from collections.abc import Callable
from typing import Any

from fastapi import WebSocket  # Added WebSocket for type hinting

# Import metrics that are directly related to the state managed here
from core_daemon.config import CONTROLLER_SOURCE_ADDR
from core_daemon.metrics import ENTITY_COUNT, HISTORY_SIZE_GAUGE
from core_daemon.models import UnknownPGNEntry, UnmappedEntryModel
from rvc_decoder.decode import load_config_data  # Changed from rvc_load_and_process_device_mapping

# To avoid circular imports, initialize this to None. Will be set in main.py
broadcast_can_sniffer_group = None  # Will be set by core_daemon.main at runtime

# In-memory state - holds the most recent data payload for each entity_id
state: dict[str, dict[str, Any]] = {}

# History duration
HISTORY_DURATION: int = 24 * 3600  # seconds
MAX_HISTORY_LENGTH: int = 1000  # Define MAX_HISTORY_LENGTH

# History data structure (initialized empty, to be populated by initialize_history_deques)
history: dict[str, deque[dict[str, Any]]] = {}

# Initialize logger
logger = logging.getLogger(__name__)

# Unmapped entries
unmapped_entries: dict[str, UnmappedEntryModel] = {}

# Unknown PGNs (PGNs not found in rvc.json spec)
unknown_pgns: dict[str, UnknownPGNEntry] = {}

# Last known brightness levels for lights
last_known_brightness_levels: dict[str, int] = {}

# Configuration data loaded at startup, to be populated by initialize_app_from_config
entity_id_lookup: dict[str, Any] = {}
light_entity_ids: list[str] = []
light_command_info: dict[str, Any] = {}
decoder_map: dict[int, Any] = {}
raw_device_mapping: dict[str, Any] = {}
device_lookup: dict[tuple, Any] = {}
status_lookup: dict[tuple, Any] = {}
pgn_hex_to_name_map: dict[str, str] = {}

# WebSocket client sets - moved here from websocket.py for central state management
clients: set[WebSocket] = set()
log_ws_clients: set[WebSocket] = set()

# CAN command/control sniffer log
can_command_sniffer_log: list = []  # Each entry: { 'timestamp', 'direction', 'arbitration_id', 'data', 'decoded', 'raw' }

# Known command/status DGN pairings for high-confidence grouping
KNOWN_COMMAND_STATUS_PAIRS: dict[str, str] = {
    # Example: '1F0D0': '1F1D0',
}

# Pending commands (TX) waiting for a response
pending_commands = []  # Each: {timestamp, instance, dgn, arbitration_id, data, ...}
# Grouped command/response pairs
can_sniffer_grouped = []  # Each: {command, response, confidence, reason}

# Set to track all observed source addresses on the CAN bus
observed_source_addresses: set[int] = set()

# For each source address, track the last-seen sniffer entry (RX or TX)
last_seen_by_source_addr: dict[int, dict] = {}

# Keep references to background tasks to prevent garbage collection
background_tasks: set[asyncio.Task] = set()

# Add global variable for coach_info
coach_info = None


def get_observed_source_addresses():
    """Returns a sorted list of all observed CAN source addresses (as ints)."""
    return sorted(observed_source_addresses)


def add_pending_command(entry: dict):
    pending_commands.append(entry)
    # Clean up old entries (older than 2s)
    now = entry["timestamp"]
    new_pending = []
    for cmd in pending_commands:
        if now - cmd["timestamp"] < 2.0:
            new_pending.append(cmd)
    pending_commands[:] = new_pending


def try_group_response(response_entry: dict):
    """
    Try to group a response (RX) with a pending command (TX).
    Returns True if grouped, False otherwise.
    """
    now = response_entry["timestamp"]
    instance = response_entry.get("instance")
    dgn = response_entry.get("dgn_hex")
    # High-confidence: mapping
    for cmd in pending_commands:
        cmd_dgn = cmd.get("dgn_hex")
        if (
            cmd.get("instance") == instance
            and isinstance(cmd_dgn, str)
            and KNOWN_COMMAND_STATUS_PAIRS.get(cmd_dgn) == dgn
            and 0 <= now - cmd["timestamp"] < 1.0
        ):
            group = {
                "command": cmd,
                "response": response_entry,
                "confidence": "high",
                "reason": "mapping",
            }
            can_sniffer_grouped.append(group)
            if broadcast_can_sniffer_group:
                task = asyncio.create_task(broadcast_can_sniffer_group(group))
                background_tasks.add(task)
                task.add_done_callback(background_tasks.discard)
            pending_commands.remove(cmd)
            return True
    # Low-confidence: heuristic (same instance, short time window, opposite direction)
    for cmd in pending_commands:
        if cmd.get("instance") == instance and 0 <= now - cmd["timestamp"] < 0.5:
            group = {
                "command": cmd,
                "response": response_entry,
                "confidence": "low",
                "reason": "heuristic",
            }
            can_sniffer_grouped.append(group)
            if broadcast_can_sniffer_group:
                task = asyncio.create_task(broadcast_can_sniffer_group(group))
                background_tasks.add(task)
                task.add_done_callback(background_tasks.discard)
            pending_commands.remove(cmd)
            return True
    return False


def get_can_sniffer_grouped():
    return list(can_sniffer_grouped)


def update_last_seen_by_source_addr(entry: dict):
    """
    Update the mapping of source address to the last-seen CAN sniffer entry.
    This enables richer device info in the network map and diagnostics.
    Args:
        entry: The CAN sniffer log entry (dict) containing at least 'source_addr'.
    """
    src = entry.get("source_addr")
    if src is not None:
        last_seen_by_source_addr[src] = entry


def add_can_sniffer_entry(entry: dict) -> None:
    """
    Adds a CAN command/control message entry to the sniffer log and updates last-seen info.
    Args:
        entry: The CAN sniffer log entry (dict).
    """
    can_command_sniffer_log.append(entry)
    update_last_seen_by_source_addr(entry)
    # Optionally limit log size
    if len(can_command_sniffer_log) > 1000:
        can_command_sniffer_log.pop(0)
    # Always notify WebSocket clients of any update (not just new addresses)
    notify_network_map_ws()


def get_can_sniffer_log() -> list:
    """
    Returns the current CAN command/control sniffer log.
    """
    return list(can_command_sniffer_log)


def initialize_app_from_config(config_data_tuple: tuple, decode_payload_function: Callable) -> None:
    """
    Initializes all configuration-derived application state.
    This function populates global variables within this module and then
    calls further initialization functions like initialize_history_deques
    and preseed_light_states.
    """
    global decoder_map, raw_device_mapping, device_lookup, status_lookup
    global light_entity_ids, entity_id_lookup, light_command_info
    global pgn_hex_to_name_map, KNOWN_COMMAND_STATUS_PAIRS
    global coach_info  # Add this global to store CoachInfo
    # Globals like state, history, etc., are modified by functions called from here (e.g., preseed)

    (
        decoder_map_val,
        raw_device_mapping_val,
        device_lookup_val,
        status_lookup_val,
        light_entity_ids_set_val,  # This is a set from load_config_data
        entity_id_lookup_val,
        light_command_info_val,
        pgn_hex_to_name_map_val,
        dgn_pairs_val,  # 9th item: dgn_pairs
        coach_info_val,  # 10th item: CoachInfo model
    ) = config_data_tuple

    # Clear and update global dictionaries
    # These ensure that if this function were ever called again, state is fresh.
    entity_id_lookup.clear()
    entity_id_lookup.update(entity_id_lookup_val)

    light_command_info.clear()
    light_command_info.update(light_command_info_val)

    device_lookup.clear()
    device_lookup.update(device_lookup_val)

    status_lookup.clear()
    status_lookup.update(status_lookup_val)

    # Assign other global config data (these are typically assigned once at startup)
    decoder_map = decoder_map_val
    raw_device_mapping = raw_device_mapping_val
    pgn_hex_to_name_map = pgn_hex_to_name_map_val
    coach_info = coach_info_val  # Store the CoachInfo model globally

    # Convert set to sorted list for light_entity_ids
    light_entity_ids = sorted(light_entity_ids_set_val)

    # Set up high-confidence DGN command/status mapping from dgn_pairs
    if dgn_pairs_val:
        KNOWN_COMMAND_STATUS_PAIRS.clear()
        for cmd_dgn, status_dgn in dgn_pairs_val.items():
            KNOWN_COMMAND_STATUS_PAIRS[cmd_dgn.upper()] = status_dgn.upper()

    logger.info("Application state populated from configuration data.")

    # These functions use the globals that were just set
    initialize_history_deques_internal()
    preseed_light_states_internal(decode_payload_function)

    logger.info("Global app_state dictionaries populated from initialize_app_from_config.")


def get_last_known_brightness(entity_id: str) -> int:
    """
    Retrieves the last known brightness for a given light entity.
    Defaults to 100 (full brightness) if not previously set.
    """
    return last_known_brightness_levels.get(entity_id, 100)


def set_last_known_brightness(entity_id: str, brightness: int) -> None:
    """
    Sets the last known brightness for a given light entity.
    Brightness should be an integer between 0 and 100.
    """
    last_known_brightness_levels[entity_id] = brightness


def initialize_history_deques_internal() -> None:
    """
    Initializes the history dictionary with empty deques for each entity ID.
    This should be called after entity_id_lookup is populated globally in this module.
    """
    global history, entity_id_lookup
    for eid in entity_id_lookup:
        if eid not in history:
            history[eid] = deque()
    logger.info("History deques initialized for all entities.")


def update_entity_state_and_history(entity_id: str, payload_to_store: dict[str, Any]) -> None:
    """
    Updates the state and history for a given entity and updates relevant metrics.

    Args:
        entity_id: The ID of the entity to update.
        payload_to_store: The complete payload dictionary to store in state and history.
    """
    global state, history, HISTORY_DURATION  # Allow modification of global state variables

    # Update current state
    state[entity_id] = payload_to_store
    ENTITY_COUNT.set(len(state))

    # Update history
    if entity_id in history:  # Should always be true if initialize_history_deques was called
        history_deque = history[entity_id]
        history_deque.append(payload_to_store)
        current_time = payload_to_store.get(
            "timestamp", time.time()
        )  # Use payload's timestamp or current time
        cutoff = current_time - HISTORY_DURATION
        while history_deque and history_deque[0]["timestamp"] < cutoff:
            history_deque.popleft()
        HISTORY_SIZE_GAUGE.labels(entity_id=entity_id).set(len(history_deque))
    else:
        # This case should ideally not be reached if entities are pre-initialized in history
        # However, as a fallback, create a new deque
        history[entity_id] = deque([payload_to_store])
        HISTORY_SIZE_GAUGE.labels(entity_id=entity_id).set(1)
        # Consider logging a warning if an entity_id is not found in history initially
        logger.warning(f"History deque not found for {entity_id}, created new one.")


def preseed_light_states_internal(decode_payload_func: Callable) -> None:
    """
    Initializes the state and history for all known light entities to an "off" state at startup.
    Uses global state variables like light_entity_ids, light_command_info, decoder_map,
    and entity_id_lookup.
    """
    global light_entity_ids, light_command_info, decoder_map, entity_id_lookup, state

    now = time.time()
    logger.info(f"Pre-seeding states for {len(light_entity_ids)} light entities.")
    for eid in light_entity_ids:
        info = light_command_info.get(eid)
        entity_config = entity_id_lookup.get(eid)

        if not info or not entity_config:
            logger.warning(f"Pre-seeding: Missing info or entity_config for light entity ID: {eid}")
            continue

        # Determine DGN for status pre-seeding:
        # Prefer status_dgn (hex string from YAML) if available.
        # Else, use the DGN from command_info (integer, under which the light is
        # defined in mapping).
        dgn_for_status_hex_str = None
        raw_status_dgn_from_config = entity_config.get("status_dgn")

        if raw_status_dgn_from_config:
            dgn_for_status_hex_str = str(raw_status_dgn_from_config).upper().replace("0X", "")
        else:
            # Fallback to the DGN the light is defined under (for commands)
            dgn_for_status_hex_str = format(info["dgn"], "X").upper()

        logger.debug(f"Pre-seeding {eid}: Using DGN {dgn_for_status_hex_str} for initial status.")

        spec_entry = None
        # Search decoder_map using the determined DGN hex string
        # decoder_map values are dictionaries from rvc.json, which contain 'dgn_hex'
        for entry_val in decoder_map.values():
            if entry_val.get("dgn_hex", "").upper().replace("0X", "") == dgn_for_status_hex_str:
                spec_entry = entry_val
                break

        if not spec_entry:
            logger.warning(
                f"Pre-seeding: No spec entry found for DGN {dgn_for_status_hex_str} (entity: {eid})"
            )
            continue

        # Assume an all-zero payload means "off" for pre-seeding
        # The length of the data should match the spec_entry's expected data length if available,
        # otherwise default to 8 bytes.
        data_length = spec_entry.get("data_length", 8)  # Assuming spec_entry might have data_length
        initial_can_payload = bytes([0] * data_length)

        decoded, raw = decode_payload_func(spec_entry, initial_can_payload)

        brightness = raw.get(
            "operating_status", 0
        )  # This might need adjustment based on actual decoded data
        human_state = "on" if brightness > 0 else "off"
        # Ensure 'lookup' is the entity_config itself, which was already fetched
        # lookup = entity_id_lookup.get(eid, {}) # This is redundant

        payload = {
            "entity_id": eid,
            "value": decoded,
            "raw": raw,
            "state": human_state,
            "timestamp": now,
            "suggested_area": entity_config.get("suggested_area", "Unknown"),
            "device_type": entity_config.get(
                "device_type", "light"
            ),  # Default to 'light' for these entities
            "capabilities": entity_config.get("capabilities", []),
            "friendly_name": entity_config.get("friendly_name"),
            "groups": entity_config.get("groups", []),
        }
        update_entity_state_and_history(eid, payload)
    logger.info("Finished pre-seeding light states.")


def populate_app_state(rvc_spec_path: str | None = None, device_mapping_path: str | None = None):
    global \
        entity_id_lookup, \
        device_lookup, \
        status_lookup, \
        light_command_info, \
        state, \
        history, \
        unknown_pgns, \
        unmapped_entries, \
        last_known_brightness_levels

    # Clear existing state
    entity_id_lookup.clear()
    device_lookup.clear()
    status_lookup.clear()
    light_command_info.clear()
    state.clear()
    history.clear()  # Clear history if it's a dict of deques
    for k in list(history.keys()):  # If history is a defaultdict(deque)
        history[k].clear()
    unknown_pgns.clear()
    unmapped_entries.clear()
    last_known_brightness_levels.clear()

    logger.info("Cleared existing application state.")  # Log after clearing

    logger.info("Attempting to load and process device mapping...")
    # Ensure this call uses the correct function name and expects the correct return structure
    processed_data_tuple = load_config_data(rvc_spec_path, device_mapping_path)
    # Unpack the tuple correctly based on what load_config_data returns
    # load_config_data returns 10 items: decoder_map, device_mapping, device_lookup, status_lookup,
    # light_entity_ids, entity_id_lookup, light_command_info, pgn_hex_to_name_map, dgn_pairs, coach_info
    # We need to map these to the structure previously assumed for processed_data or adjust
    (
        _decoder_map,  # We might not need all of these directly in populate_app_state
        _device_mapping_yaml,
        loaded_device_lookup,
        loaded_status_lookup,
        _light_entity_ids,  # This is a set, light_command_info keys can serve a similar purpose
        loaded_entity_id_lookup,
        loaded_light_command_info,
        _pgn_hex_to_name_map,
        _dgn_pairs,  # Added 9th item
        _coach_info,  # Added 10th item
    ) = processed_data_tuple

    # Populate from processed_data
    entity_id_lookup.update(loaded_entity_id_lookup)
    device_lookup.update(loaded_device_lookup)
    status_lookup.update(loaded_status_lookup)
    light_command_info.update(loaded_light_command_info)
    # Note: The original `processed_data` was a dict. `load_config_data` returns a tuple.
    # The logic here now correctly unpacks the tuple and updates the global dicts.

    logger.info(
        f"After rvc_load_mapping: app_state.entity_id_lookup has {len(entity_id_lookup)} entries."
    )
    logger.info(
        f"After rvc_load_mapping: app_state.light_command_info has "
        f"{len(light_command_info)} entries."
    )

    # Initialize history deques for all known entities from entity_id_lookup
    for eid in entity_id_lookup:
        if eid not in history:  # Check if deque already exists (e.g. from previous partial load)
            history[eid] = deque(maxlen=MAX_HISTORY_LENGTH)
    logger.info("History deques initialized for all entities.")

    # Pre-seeding states
    startup_time = time.time()
    logger.info(f"Pre-seeding states for {len(light_command_info)} light entities.")
    for eid, lci_entry in light_command_info.items():
        # ... (existing pre-seeding logic for lights)
        # Ensure entity_id_lookup[eid] is safe to access here
        if eid in entity_id_lookup:
            lookup_data = entity_id_lookup[eid]
            initial_payload_to_store = {
                "entity_id": eid,
                "value": {
                    "operating_status": "0",
                    "instance": str(lci_entry.get("instance")),
                    "group": str(lci_entry.get("group_mask")),
                },
                "raw": {
                    "operating_status": 0,
                    "instance": lci_entry.get("instance"),
                    "group": lci_entry.get("group_mask"),
                },
                "state": "off",  # Default to off
                "timestamp": startup_time,
                "suggested_area": lookup_data.get("suggested_area", "Unknown"),
                "device_type": lookup_data.get("device_type", "light"),
                "capabilities": lookup_data.get("capabilities", []),
                "friendly_name": lookup_data.get("friendly_name", eid),
                "groups": lookup_data.get("groups", []),
                "interface": lookup_data.get("interface", "unknown"),  # Added interface
                "status_dgn": lookup_data.get("status_dgn", "unknown"),  # Added status_dgn
                "command_dgn": lci_entry.get(
                    "dgn", "unknown"
                ),  # Added command_dgn from light_command_info
            }
            state[eid] = initial_payload_to_store
            history[eid].append(initial_payload_to_store)
            if eid not in last_known_brightness_levels:  # Initialize last known brightness
                set_last_known_brightness(eid, 100)  # Default to 100 when turned on
        else:
            logger.warning(
                f"Pre-seeding: Entity ID '{eid}' from light_command_info not "
                f"found in entity_id_lookup."
            )

    logger.info("Finished pre-seeding light states.")
    # ... (pre-seeding for other device types if any) ...

    logger.info("Application state fully populated and pre-seeded by populate_app_state.")


def notify_network_map_ws():
    """Call this after adding a new source address to broadcast to WebSocket clients."""
    try:
        import asyncio

        from core_daemon.websocket import broadcast_network_map

        loop = asyncio.get_event_loop()
        if loop.is_running():
            task = loop.create_task(broadcast_network_map())
            background_tasks.add(task)
            task.add_done_callback(background_tasks.discard)
    except Exception:
        pass


def get_controller_source_addr():
    """Returns the controller's source address as an int."""
    return CONTROLLER_SOURCE_ADDR
