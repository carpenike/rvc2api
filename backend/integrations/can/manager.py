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
import time

import can
from can.bus import BusABC
from can.exceptions import CanInterfaceNotImplementedError

from backend.services.app_state import (
    add_can_sniffer_entry,
    add_pending_command,
    decoder_map,
    get_controller_source_addr,
)
from backend.services.metrics import CAN_TX_QUEUE_LENGTH
from backend.services.rvc_decoder import decode_payload

logger = logging.getLogger(__name__)

can_tx_queue: asyncio.Queue[tuple[can.Message, str]] = asyncio.Queue()
buses: dict[str, BusABC] = {}


async def can_writer() -> None:
    """
    Continuously dequeues messages from can_tx_queue and sends them over the CAN bus.
    Handles sending each message twice as per RV-C specification.
    Attempts to initialize a bus if not already available in the 'buses' dictionary.
    """
    default_bustype = os.getenv("CAN_BUSTYPE", "socketcan")
    while True:
        msg, interface_name = await can_tx_queue.get()
        CAN_TX_QUEUE_LENGTH.set(can_tx_queue.qsize())
        try:
            bus = buses.get(interface_name)
            if not bus:
                logger.warning(
                    f"CAN writer: Bus for interface '{interface_name}' not pre-initialized. "
                    f"Attempting to open with bustype '{default_bustype}'."
                )
                try:
                    bus = can.interface.Bus(channel=interface_name, bustype=default_bustype)
                    buses[interface_name] = bus
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
                entry = decoder_map.get(msg.arbitration_id)
                instance = None
                decoded = None
                raw = None
                try:
                    if entry:
                        decoded, raw = decode_payload(entry, msg.data)
                        instance = raw.get("instance") if raw else None
                except Exception:
                    pass
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
                await asyncio.sleep(0.05)  # RV-C spec: send commands twice
                bus.send(msg)
                logger.info(
                    f"CAN TX (2/2): {interface_name} ID: {msg.arbitration_id:08X} "
                    f"Data: {msg.data.hex().upper()}"
                )
            except can.exceptions.CanError as e:
                logger.error(f"CAN writer failed to send message on {interface_name}: {e}")
            except Exception as e:
                logger.error(
                    f"CAN writer encountered an unexpected error "
                    f"during send on {interface_name}: {e}"
                )
        except Exception as e:
            logger.error(
                f"CAN writer encountered a critical unexpected error for {interface_name}: {e}",
                exc_info=True,
            )
        finally:
            can_tx_queue.task_done()
            CAN_TX_QUEUE_LENGTH.set(can_tx_queue.qsize())
