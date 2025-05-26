"""
Manages CAN bus communication for the rvc2api daemon.

This module is responsible for:
- Initializing and managing CAN bus listener threads for specified interfaces.
- Providing a writer task to send messages from an asynchronous queue to the CAN bus.
- Constructing RV-C specific CAN messages (e.g., for light control).
- Storing and providing access to active CAN bus interface objects.
"""

import asyncio
import logging
import os
import threading
import time
from collections.abc import Callable

import can
from can.bus import BusABC
from can.exceptions import CanInterfaceNotImplementedError  # For more specific error handling

from core_daemon.app_state import (
    add_can_sniffer_entry,
    add_pending_command,
    get_controller_source_addr,
)

# Import specific metrics used by can_writer
from core_daemon.metrics import CAN_TX_QUEUE_LENGTH

logger = logging.getLogger(__name__)

# Global CAN transmit queue, to be used by other modules (e.g., main.py)
can_tx_queue: asyncio.Queue[tuple[can.Message, str]] = asyncio.Queue()

# Dictionary to hold active CAN bus interfaces, keyed by interface name.
# This is populated by initialize_can_listeners and used by can_writer.
buses: dict[str, BusABC] = {}


async def can_writer():
    """
    Continuously dequeues messages from can_tx_queue and sends them over the CAN bus.
    Handles sending each message twice as per RV-C specification.
    Attempts to initialize a bus if not already available in the 'buses' dictionary.
    """
    # It's better to get CAN_BUSTYPE once, or ensure it's passed if it can change.
    # For now, assuming it's relatively static during the daemon's lifecycle.
    default_bustype = os.getenv("CAN_BUSTYPE", "socketcan")

    while True:
        msg, interface_name = await can_tx_queue.get()
        CAN_TX_QUEUE_LENGTH.set(can_tx_queue.qsize())

        try:
            bus = buses.get(interface_name)
            if not bus:
                # This block is a fallback. Ideally, start_can_readers in main.py
                # should have already initialized and populated the bus in the 'buses' dict.
                logger.warning(
                    f"CAN writer: Bus for interface '{interface_name}' not pre-initialized. "
                    f"Attempting to open with bustype '{default_bustype}'."
                )
                try:
                    # Note: Bitrate is not known here. This could be an issue if not using a
                    # bus type that auto-detects or if a specific bitrate is required
                    # and differs from what start_can_readers would use.
                    # For socketcan, bitrate is usually set at the OS level.
                    bus = can.interface.Bus(channel=interface_name, bustype=default_bustype)
                    buses[interface_name] = bus  # Add to shared buses dict
                    logger.info(
                        f"CAN writer: Successfully opened and "
                        f"registered bus for '{interface_name}'."
                    )
                except CanInterfaceNotImplementedError as e:
                    logger.error(
                        f"CAN writer: CAN interface '{interface_name}' ({default_bustype}) "
                        f"is not implemented or configuration is missing: {e}"
                    )
                    can_tx_queue.task_done()
                    continue
                except Exception as e:
                    logger.error(
                        f"CAN writer: Failed to initialize CAN bus '{interface_name}' "
                        f"({default_bustype}): {e}"
                    )
                    can_tx_queue.task_done()
                    continue

            try:
                bus.send(msg)
                logger.info(
                    f"CAN TX (1/2): {interface_name} ID: {msg.arbitration_id:08X} "
                    f"Data: {msg.data.hex().upper()}"
                )
                # --- CAN Sniffer Logging (TX, ALL messages) ---
                now = time.time()
                from core_daemon.app_state import decoder_map

                entry = decoder_map.get(msg.arbitration_id)
                instance = None
                decoded = None
                raw = None
                try:
                    if entry:
                        from rvc_decoder import decode_payload

                        decoded, raw = decode_payload(entry, msg.data)
                        instance = raw.get("instance")
                except Exception:
                    pass
                # Use configurable controller source address
                source_addr = msg.arbitration_id & 0xFF
                origin = "self" if source_addr == get_controller_source_addr() else "other"
                sniffer_entry = {
                    "timestamp": now,
                    "direction": "tx",
                    "arbitration_id": msg.arbitration_id,
                    "data": msg.data.hex().upper(),
                    "decoded": decoded,
                    "raw": raw,
                    "iface": interface_name,
                    "pgn": entry.get("pgn") if entry else None,
                    "dgn_hex": entry.get("dgn_hex") if entry else None,
                    "name": entry.get("name") if entry else None,
                    "instance": instance,
                    "source_addr": source_addr,
                    "origin": origin,
                }
                add_can_sniffer_entry(sniffer_entry)
                add_pending_command(sniffer_entry)
                # --- END CAN Sniffer Logging ---
                await asyncio.sleep(0.05)  # RV-C spec: send commands twice
                bus.send(msg)
                logger.info(
                    f"CAN TX (2/2): {interface_name} ID: {msg.arbitration_id:08X} "
                    f"Data: {msg.data.hex().upper()}"
                )
            except can.exceptions.CanError as e:  # More specific CAN error
                logger.error(f"CAN writer failed to send message on {interface_name}: {e}")
                # Optionally, consider removing or re-initializing the bus from 'buses' dict
                # if the error is persistent (e.g., bus down).
                # For now, we'll just log and continue.
            except Exception as e:
                logger.error(
                    f"CAN writer encountered an unexpected error "
                    f"during send on {interface_name}: {e}"
                )

        except Exception as e:
            # Catch-all for unexpected errors in the outer try (e.g., issues with bus retrieval)
            logger.error(
                f"CAN writer encountered a critical unexpected error for {interface_name}: {e}",
                exc_info=True,
            )
        finally:
            can_tx_queue.task_done()
            CAN_TX_QUEUE_LENGTH.set(can_tx_queue.qsize())  # Update queue size metric


def initialize_can_writer_task():
    """
    Creates and schedules the CAN writer asyncio task.
    """
    writer_task = asyncio.create_task(can_writer())
    logger.info("CAN writer task initialized and scheduled to run.")
    return writer_task


def initialize_can_listeners(
    interfaces: list[str],
    bustype: str,
    bitrate: int,
    message_handler_callback: Callable,  # Callback for processing received messages
    logger_instance: logging.Logger,  # Pass logger for consistent logging
    # loop: asyncio.AbstractEventLoop, # To call threadsafe methods on the callback if it's async
) -> None:
    """
    Initializes and starts CAN listener threads for each specified interface.

    Args:
        interfaces: A list of CAN interface names (e.g., ['can0', 'can1']).
        bustype: The type of CAN bus (e.g., 'socketcan', 'pcan').
        bitrate: The bitrate for the CAN bus.
        message_handler_callback: A function to be called when a message is received.
                                  It should accept (can.Message, str_interface_name).
        logger_instance: The logger instance to use for logging within the listeners.
    """
    import platform

    global buses  # Ensure we are using the global buses dictionary

    # Check for platform compatibility
    is_linux = platform.system() == "Linux"
    if not is_linux and bustype == "socketcan":
        logger_instance.warning(
            f"socketcan is not supported on {platform.system()}. "
            f"CAN listeners will not be started. "
            f"Consider using a virtual CAN interface for development."
        )
        return

    if not interfaces:
        logger_instance.warning("No CAN interfaces specified. CAN listeners will not be started.")
        return

    logger_instance.info(
        f"Preparing CAN listeners for interfaces: {interfaces}, "
        f"bustype: {bustype}, bitrate: {bitrate}bps"
    )

    def reader_thread_target(iface_name: str) -> None:
        # 'message_handler_callback' is available from the outer scope
        # 'logger_instance' is available from the outer scope
        # 'buses' is global
        try:
            bus = can.interface.Bus(channel=iface_name, bustype=bustype, bitrate=bitrate)
            buses[iface_name] = bus  # Store the initialized bus
            logger_instance.info(
                f"CAN listener started on {iface_name} via {bustype} @ {bitrate}bps"
            )
        except CanInterfaceNotImplementedError as e:
            logger_instance.error(
                f"Cannot open CAN bus '{iface_name}' ({bustype}, {bitrate}bps): {e}"
            )
            return
        except Exception as e:
            logger_instance.error(
                f"Failed to initialize CAN bus '{iface_name}' ({bustype}, "
                f"{bitrate}bps) due to an unexpected error: {e}"
            )
            return

        while True:
            try:
                msg = bus.recv(timeout=1.0)  # Timeout allows thread to be responsive
                if msg is not None:
                    # Call the provided callback to process the message.
                    # The callback will be defined in main.py and will handle its own
                    # asyncio interactions (e.g., loop.call_soon_threadsafe for broadcasts).
                    message_handler_callback(msg, iface_name)
            except Exception as e_reader_loop:
                logger_instance.error(
                    f"CRITICAL ERROR IN CAN LISTENER LOOP for {iface_name}: {e_reader_loop}",
                    exc_info=True,
                )
                # Add a small delay to prevent log spamming if the error is persistent
                # and the bus might be down or in a problematic state.
                time.sleep(1)

    for iface in interfaces:
        thread = threading.Thread(target=reader_thread_target, args=(iface,), daemon=True)
        thread.start()
    logger_instance.info(f"{len(interfaces)} CAN listener(s) initialized and started.")


def create_light_can_message(pgn: int, instance: int, brightness_can_level: int) -> can.Message:
    """
    Constructs a can.Message for an RV-C light command.

    Args:
        pgn: The Parameter Group Number for the light command.
        instance: The instance ID of the light.
        brightness_can_level: The target brightness level, scaled for CAN (e.g., 0-200).

    Returns:
        A can.Message object ready to be sent.
    """
    # Determine Arbitration ID components
    prio = 6  # Typical priority for commands
    sa = 0xF9  # Source Address (typically the controller/gateway)
    dp = (pgn >> 16) & 1  # Data Page
    pf = (pgn >> 8) & 0xFF  # PDU Format
    da = 0xFF  # Destination Address (broadcast)

    if pf < 0xF0:  # PDU1 format (destination address is DA)
        arbitration_id = (prio << 26) | (dp << 24) | (pf << 16) | (da << 8) | sa
    else:  # PDU2 format (destination address is in PS field, effectively broadcast if DA is 0xFF)
        ps = pgn & 0xFF  # PDU Specific (contains group extension or specific address)
        arbitration_id = (prio << 26) | (dp << 24) | (pf << 16) | (ps << 8) | sa

    # Construct payload
    payload_data = bytes(
        [
            instance,  # Instance
            0x7C,  # Group Mask (typically 0x7C for DML_COMMAND_2 based lights)
            brightness_can_level,  # Level (0-200, 0xC8 for 100%)
            0x00,  # Command: SetLevel
            0x00,  # Duration: Instantaneous
            0xFF,  # Reserved
            0xFF,  # Reserved
            0xFF,  # Reserved
        ]
    )

    return can.Message(arbitration_id=arbitration_id, data=payload_data, is_extended_id=True)
