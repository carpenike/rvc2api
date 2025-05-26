"""
Handles the processing of incoming CAN messages for the rvc2api daemon.

This module is responsible for:
- Receiving raw CAN messages.
- Looking up decoder information based on the message's arbitration ID.
- Decoding the message payload using the `rvc_decoder`.
- Updating the application state (`app_state`) with the decoded data.
- Handling messages that cannot be mapped to known entities.
- Broadcasting processed data to WebSocket clients.
- Recording relevant metrics.
"""

import asyncio
import json

# Logging - assuming logger is passed or configured globally
import logging
import time
from typing import Any

import can

# Imports from rvc_decoder
from rvc_decoder import decode_payload  # Assuming this is accessible

# Imports from app_state
from core_daemon.app_state import (
    add_can_sniffer_entry,
    entity_id_lookup,
    try_group_response,
    unknown_pgns,  # Add unknown_pgns
    unmapped_entries,
    update_entity_state_and_history,
)

# Imports from metrics
from core_daemon.metrics import (
    DECODE_ERRORS,
    DGN_TYPE_GAUGE,
    FRAME_COUNTER,
    FRAME_LATENCY,
    GENERATOR_COMMAND_COUNTER,
    GENERATOR_DEMAND_COMMAND_COUNTER,
    GENERATOR_STATUS_1_COUNTER,
    GENERATOR_STATUS_2_COUNTER,
    INST_USAGE_COUNTER,
    LOOKUP_MISSES,
    PGN_USAGE_COUNTER,
    SUCCESSFUL_DECODES,
)

# Imports from models
from core_daemon.models import (
    SuggestedMapping,  # Add UnknownPGNEntry
    UnknownPGNEntry,
    UnmappedEntryModel,
)

# Imports from websocket
from core_daemon.websocket import broadcast_to_clients

logger = logging.getLogger(__name__)


def process_can_message(
    msg: can.Message,
    iface_name: str,
    loop: asyncio.AbstractEventLoop,
    decoder_map: dict,  # Passed as argument
    device_lookup: dict,  # Passed as argument
    status_lookup: dict,  # Passed as argument
    pgn_hex_to_name_map: dict,  # Passed as argument
    raw_device_mapping: dict,  # Passed as argument
):
    if msg.arbitration_id == 536861658:  # GENERATOR_COMMAND
        GENERATOR_COMMAND_COUNTER.inc()
    elif msg.arbitration_id == 436198557:  # GENERATOR_STATUS_1
        GENERATOR_STATUS_1_COUNTER.inc()
    elif msg.arbitration_id == 536861659:  # GENERATOR_STATUS_2
        GENERATOR_STATUS_2_COUNTER.inc()
    elif msg.arbitration_id == 536870895:  # GENERATOR_DEMAND_COMMAND
        GENERATOR_DEMAND_COMMAND_COUNTER.inc()

    FRAME_COUNTER.inc()
    start_time = time.perf_counter()
    decoded_payload_for_unmapped: dict[str, Any] | None = None
    entry = decoder_map.get(msg.arbitration_id)

    try:
        if not entry:
            LOOKUP_MISSES.inc()
            # --- MODIFICATION START: Handle PGNs not in rvc.json spec ---
            arb_id_hex = f"{msg.arbitration_id:X}"
            now_ts = time.time()

            if arb_id_hex not in unknown_pgns:
                unknown_pgns[arb_id_hex] = UnknownPGNEntry(
                    arbitration_id_hex=arb_id_hex,
                    first_seen_timestamp=now_ts,
                    last_seen_timestamp=now_ts,
                    count=1,
                    last_data_hex=msg.data.hex().upper(),
                )
            else:
                current_unknown = unknown_pgns[arb_id_hex]
                current_unknown.last_seen_timestamp = now_ts
                current_unknown.count += 1
                current_unknown.last_data_hex = msg.data.hex().upper()
            # --- NEW: Track all observed source addresses ---
            from core_daemon.app_state import notify_network_map_ws, observed_source_addresses

            source_addr = msg.arbitration_id & 0xFF
            if source_addr not in observed_source_addresses:
                observed_source_addresses.add(source_addr)
                notify_network_map_ws()
            # --- MODIFICATION END ---

            # --- NEW: Always add a sniffer entry for all RX messages ---
            sniffer_entry = {
                "timestamp": now_ts,
                "direction": "rx",
                "arbitration_id": msg.arbitration_id,
                "data": msg.data.hex().upper(),
                "decoded": None,
                "raw": None,
                "iface": iface_name,
                "pgn": None,
                "dgn_hex": None,
                "name": None,
                "instance": None,
                "source_addr": source_addr,
            }
            add_can_sniffer_entry(sniffer_entry)
            return  # Return after handling unknown PGN

        decoded, raw = decode_payload(entry, msg.data)
        decoded_payload_for_unmapped = decoded
        SUCCESSFUL_DECODES.inc()

        # --- CAN Command/Control Sniffer Logging (RX/TX + Grouping, all sources) ---
        is_command = (
            entry.get("name", "").lower().find("command") != -1
            or entry.get("name", "").lower().find("control") != -1
        )
        now = time.time()
        instance = raw.get("instance")
        dgn_hex = entry.get("dgn_hex")
        # Extract source address from arbitration ID (last byte for typical RV-C)
        source_addr = msg.arbitration_id & 0xFF
        # --- NEW: Track all observed source addresses ---
        from core_daemon.app_state import notify_network_map_ws, observed_source_addresses

        if source_addr not in observed_source_addresses:
            observed_source_addresses.add(source_addr)
            notify_network_map_ws()
        sniffer_entry = {
            "timestamp": now,
            "direction": "rx",
            "arbitration_id": msg.arbitration_id,
            "data": msg.data.hex().upper(),
            "decoded": decoded,
            "raw": raw,
            "iface": iface_name,
            "pgn": entry.get("pgn"),
            "dgn_hex": dgn_hex,
            "name": entry.get("name"),
            "instance": instance,
            "source_addr": source_addr,
        }
        if is_command:
            # Log ALL command/control messages, regardless of source
            add_can_sniffer_entry(sniffer_entry)
        else:
            # Try to group as a response
            grouped = try_group_response(sniffer_entry)
            if not grouped:
                add_can_sniffer_entry(sniffer_entry)
        # --- END CAN Command/Control Sniffer Logging ---

    except Exception as e:
        logger.error(
            f"Decode error for PGN 0x{msg.arbitration_id:X} on {iface_name}: {e}",
            exc_info=True,
        )
        DECODE_ERRORS.inc()
        return
    finally:
        FRAME_LATENCY.observe(time.perf_counter() - start_time)

    dgn = entry.get("dgn_hex")
    inst = raw.get("instance")

    if not dgn or inst is None:
        LOOKUP_MISSES.inc()
        logger.debug(
            f"DGN or instance missing in decoded payload for PGN "
            f"0x{msg.arbitration_id:X} (Spec DGN: {entry.get('dgn_hex')}). "
            f"DGN from payload: {dgn}, Instance from payload: {inst}"
        )
        return

    key = (dgn.upper(), str(inst))
    matching_devices = [dev for k, dev in status_lookup.items() if k == key]
    if not matching_devices:
        default_key = (dgn.upper(), "default")
        if default_key in status_lookup:
            matching_devices = [status_lookup[default_key]]
    if not matching_devices:
        if key in device_lookup:
            matching_devices = [device_lookup[key]]
        elif (dgn.upper(), "default") in device_lookup:
            matching_devices = [device_lookup[(dgn.upper(), "default")]]

    if not matching_devices:
        LOOKUP_MISSES.inc()
        logger.debug(f"No device config for DGN={dgn}, Inst={inst} (PGN 0x{msg.arbitration_id:X})")

        unmapped_key_str = f"{dgn.upper()}-{inst!s}"
        model_pgn_hex = f"{(msg.arbitration_id >> 8) & 0x3FFFF:X}".upper()
        model_pgn_name = pgn_hex_to_name_map.get(model_pgn_hex)
        model_dgn_hex = dgn.upper()
        model_dgn_name = entry.get("name")
        now_ts = time.time()
        suggestions_list = []
        if raw_device_mapping and isinstance(raw_device_mapping.get("devices"), list):
            for device_config in raw_device_mapping["devices"]:
                if device_config.get("dgn_hex", "").upper() == dgn.upper() and str(
                    device_config.get("instance")
                ) != str(inst):
                    suggestions_list.append(
                        SuggestedMapping(
                            instance=str(device_config.get("instance")),
                            name=device_config.get("name", "Unknown Name"),
                            suggested_area=device_config.get("suggested_area"),
                        )
                    )

        if unmapped_key_str not in unmapped_entries:
            unmapped_entries[unmapped_key_str] = UnmappedEntryModel(
                pgn_hex=model_pgn_hex,
                pgn_name=model_pgn_name,
                dgn_hex=model_dgn_hex,
                dgn_name=model_dgn_name,
                instance=str(inst),
                last_data_hex=msg.data.hex().upper(),
                decoded_signals=decoded_payload_for_unmapped,
                first_seen_timestamp=now_ts,
                last_seen_timestamp=now_ts,
                count=1,
                suggestions=suggestions_list if suggestions_list else None,
                spec_entry=entry,
            )
        else:
            current_unmapped = unmapped_entries[unmapped_key_str]
            current_unmapped.last_data_hex = msg.data.hex().upper()
            current_unmapped.decoded_signals = decoded_payload_for_unmapped
            current_unmapped.last_seen_timestamp = now_ts
            current_unmapped.count += 1
            if model_pgn_name and not current_unmapped.pgn_name:
                current_unmapped.pgn_name = model_pgn_name
            if model_dgn_name and not current_unmapped.dgn_name:
                current_unmapped.dgn_name = model_dgn_name
            if entry and not current_unmapped.spec_entry:
                current_unmapped.spec_entry = entry
            if not current_unmapped.suggestions and suggestions_list:
                current_unmapped.suggestions = suggestions_list
        return

    ts = time.time()
    raw_brightness = raw.get("operating_status", 0)
    state_str = "on" if raw_brightness > 0 else "off"

    for device in matching_devices:
        eid = device["entity_id"]
        lookup_data = entity_id_lookup.get(eid, {})  # Changed from app_state.entity_id_lookup
        payload = {
            "entity_id": eid,
            "value": decoded,
            "raw": raw,
            "state": state_str,
            "timestamp": ts,
            "suggested_area": lookup_data.get("suggested_area", "Unknown"),
            "device_type": lookup_data.get("device_type", "unknown"),
            "capabilities": lookup_data.get("capabilities", []),
            "friendly_name": lookup_data.get("friendly_name"),
            "groups": lookup_data.get("groups", []),
        }
        pgn_val = msg.arbitration_id & 0x3FFFF
        PGN_USAGE_COUNTER.labels(pgn=f"{pgn_val:X}").inc()
        INST_USAGE_COUNTER.labels(dgn=dgn.upper(), instance=str(inst)).inc()
        device_type = device.get("device_type", "unknown")
        DGN_TYPE_GAUGE.labels(device_type=device_type).set(1)

        update_entity_state_and_history(eid, payload)

        text = json.dumps(payload)
        if loop and loop.is_running():
            target_coro = broadcast_to_clients(text)
            loop.call_soon_threadsafe(loop.create_task, target_coro)

        SUCCESSFUL_DECODES.inc()
