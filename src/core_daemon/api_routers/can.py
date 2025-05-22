"""
Defines FastAPI APIRouter for CAN bus related operations.

This module includes routes to get the status of CAN interfaces,
check the CAN transmit queue, and CAN sniffer endpoints.
"""

import asyncio
import logging
import platform
from typing import Any

from fastapi import APIRouter, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from core_daemon.app_state import get_can_sniffer_grouped
from core_daemon.can_manager import buses, can_tx_queue
from core_daemon.models import AllCANStats, CANInterfaceStats
from core_daemon.websocket import network_map_ws_endpoint

# Conditionally import pyroute2 only on Linux systems
# This allows development on macOS without pyroute2 installed
CAN_SUPPORTED = platform.system() == "Linux"
if CAN_SUPPORTED:
    try:
        from pyroute2 import IPRoute  # type: ignore
    except ImportError:
        IPRoute = None
        CAN_SUPPORTED = False
else:
    IPRoute = None

logger = logging.getLogger(__name__)

api_router_can = APIRouter()  # FastAPI router for CAN-related endpoints

# In-memory set of WebSocket clients for scan results
canbus_scan_ws_clients = set()


@api_router_can.websocket("/ws/canbus-scan")
async def canbus_scan_ws(websocket: WebSocket):
    await websocket.accept()
    canbus_scan_ws_clients.add(websocket)
    try:
        while True:
            # Keep the connection open; actual scan results will be pushed from the scan task
            await asyncio.sleep(60)
    except WebSocketDisconnect:
        canbus_scan_ws_clients.remove(websocket)


# Utility function to broadcast scan results to all connected clients
async def broadcast_canbus_scan_result(result):
    to_remove = set()
    for ws in canbus_scan_ws_clients:
        try:
            await ws.send_json(result)
        except Exception:
            to_remove.add(ws)
    for ws in to_remove:
        canbus_scan_ws_clients.remove(ws)


def get_stats_from_pyroute2_link(link: Any) -> CANInterfaceStats:
    """
    Populates a CANInterfaceStats object from pyroute2 link data.

    Args:
        link: A dictionary representing a network interface from pyroute2.

    Returns:
        A CANInterfaceStats object.
    """
    interface_name = link.get_attr("IFLA_IFNAME")
    stats = CANInterfaceStats(name=interface_name)

    stats.state = link.get_attr("IFLA_OPERSTATE")  # General operstate (UP, DOWN, UNKNOWN etc)

    if link.get_attr("IFLA_LINKMODE") == 1:  # LINKMODE_DORMANT is 1, LINKMODE_DEFAULT is 0
        stats.state = "DORMANT"  # More specific if link is DORMANT

    # Statistics are usually under IFLA_STATS or IFLA_STATS64
    link_stats = link.get_attr("IFLA_STATS64") or link.get_attr("IFLA_STATS")
    if link_stats:
        stats.rx_packets = link_stats.get("rx_packets")
        stats.tx_packets = link_stats.get("tx_packets")
        stats.rx_bytes = link_stats.get("rx_bytes")
        stats.tx_bytes = link_stats.get("tx_bytes")
        stats.rx_errors = link_stats.get("rx_errors")
        stats.tx_errors = link_stats.get("tx_errors")
        # pyroute2 stats names are fairly direct: 'rx_dropped', 'tx_dropped', 'multicast',
        # 'collisions', 'rx_crc_errors', 'rx_frame_errors', 'rx_fifo_errors',
        # 'rx_missed_errors', etc. 'tx_aborted_errors', 'tx_carrier_errors',
        # 'tx_fifo_errors', 'tx_heartbeat_errors', 'tx_window_errors'
        # These are general interface stats, not CAN specific error counters like bus_off,
        # error_passive etc.

    # CAN specific details are often in IFLA_LINKINFO -> INFO_DATA
    linkinfo = link.get("linkinfo")
    if linkinfo and linkinfo.get_attr("IFLA_INFO_KIND") == "can":
        info_data = linkinfo.get("info_data")
        if info_data:
            stats.bitrate = info_data.get_attr("CAN_BITTIMING_BITRATE")
            # sample_point is often in permille (1/1000)
            stats.sample_point = info_data.get_attr("CAN_BITTIMING_SAMPLE_POINT") / 1000.0
            # stats.tq = info_data.get_attr('CAN_BITTIMING_TQ')
            # stats.prop_seg = info_data.get_attr('CAN_BITTIMING_PROP_SEG')
            # stats.phase_seg1 = info_data.get_attr('CAN_BITTIMING_PHASE_SEG1')
            # stats.phase_seg2 = info_data.get_attr('CAN_BITTIMING_PHASE_SEG2')
            # stats.sjw = info_data.get_attr('CAN_BITTIMING_SJW')
            # stats.brp = info_data.get_attr('CAN_BITTIMING_BRP')

            # CAN controller mode details
            # ctrlmode = info_data.get_attr('CAN_CTRLMODE')
            # if ctrlmode:
            #     stats.loopback = bool(ctrlmode & CAN_CTRLMODE_LOOPBACK)
            #     stats.listen_only = bool(ctrlmode & CAN_CTRLMODE_LISTENONLY)
            #     stats.triple_sampling = bool(ctrlmode & CAN_CTRLMODE_3_SAMPLES)
            #     stats.one_shot = bool(ctrlmode & CAN_CTRLMODE_ONE_SHOT)
            #     stats.berr_reporting = bool(ctrlmode & CAN_CTRLMODE_BERR_REPORTING)

            # CAN state (ERROR-ACTIVE, ERROR-WARNING, ERROR-PASSIVE, BUS-OFF)
            can_state_val = info_data.get_attr("CAN_STATE")
            if can_state_val is not None:
                # pyroute2 provides integer constants for these states
                # from pyroute2.netlink.rtnl.ifinfmsg import CAN_STATE
                # Example: CAN_STATE_ERROR_ACTIVE = 0, CAN_STATE_ERROR_WARNING = 1, etc.
                # Mapping these integers to string representations:
                can_state_map = {
                    0: "ERROR-ACTIVE",
                    1: "ERROR-WARNING",
                    2: "ERROR-PASSIVE",
                    3: "BUS-OFF",
                    4: "STOPPED",
                    5: "SLEEPING",
                }
                stats.state = can_state_map.get(
                    can_state_val, stats.state
                )  # Override general state

            # CAN specific error counters (these might be under IFLA_XSTATS)
            # xstats = link.get_attr('IFLA_XSTATS')
            # if xstats and xstats.get_attr('LINK_XSTATS_TYPE') == IFLA_XSTATS_LINK_CAN:
            #    stats.bus_errors = xstats.get_attr('can_stats_bus_error')
            #    stats.error_warning = xstats.get_attr('can_stats_error_warning')
            #    stats.error_passive = xstats.get_attr('can_stats_error_passive')
            #    stats.bus_off = xstats.get_attr('can_stats_bus_off')
            #    stats.restarts = xstats.get_attr('can_stats_restarts')
            # Accessing CAN error counters (bus_off_cnt, error_passive_cnt, etc.)
            # via IFLA_LINKINFO -> INFO_DATA -> CAN_BERR_COUNTER might be more reliable.
            berr_counter = info_data.get_attr("CAN_BERR_COUNTER")
            if berr_counter:
                # These are receive and transmit error counters, not state counters.
                # stats.rx_errors_can = berr_counter.get('rxerr')
                # stats.tx_errors_can = berr_counter.get('txerr')
                pass  # Placeholder for more detailed CAN error counter parsing

            # Clock frequency
            # clock_info = info_data.get_attr('CAN_CLOCK')
            # if clock_info:
            #    stats.clock_freq = clock_info.get('freq')

    # For fields like promiscuity, allmulti, parentbus, parentdev,
    # these are attributes of the link itself.
    stats.promiscuity = link.get_attr("IFLA_PROMISCUITY")
    # stats.allmulti = link.get_attr('IFLA_ALLMULTI')

    # Parent device info
    # master_idx = link.get_attr('IFLA_MASTER')
    # if master_idx:
    #    try:
    #        with IPRoute() as ipr_master:
    #            master_link = ipr_master.get_links(master_idx)
    #            if master_link:
    #                stats.parentdev = master_link[0].get_attr('IFLA_IFNAME')
    #    except Exception as e:
    #        logger.warning(f"Could not get master link name for {interface_name}: {e}")

    # Note: Some fields like restart_ms, tq, prop_seg, etc. from `ip -details`
    # are derived or specific to the `ip` command's interpretation and might not
    # be directly available as separate attributes in pyroute2's raw netlink data.
    # They are part of the CAN_BITTIMING structure but pyroute2 might not expose
    # them individually without deeper parsing of raw netlink messages or if they
    # are not standard attributes.

    return stats


async def get_can_interfaces_pyroute2() -> list[str]:
    """
    Lists available CAN interfaces using pyroute2.

    Returns:
        A list of CAN interface names (e.g., ["can0", "can1"]), or an empty
        list if none are found or an error occurs.
    """
    interfaces = []
    if not CAN_SUPPORTED or IPRoute is None:
        logger.debug("Cannot list CAN interfaces: pyroute2 not available or not on Linux")
        return []

    try:
        with IPRoute() as ipr:
            # Get links of type 'can'.
            # Modern pyroute2 should support kind filtering.
            links = ipr.get_links(kind="can")
            for link in links:
                interfaces.append(link.get_attr("IFLA_IFNAME"))
        return interfaces
    except Exception as e:
        logger.error(f"Error listing CAN interfaces with pyroute2: {e}", exc_info=True)
        return []


@api_router_can.get("/can/status", response_model=AllCANStats)
async def get_can_status():
    """
    Retrieves detailed status for all CAN interfaces the service is listening on.
    Combines pyroute2 stats (if available) with the actual set of active interfaces.
    On non-Linux platforms, returns a platform-specific message.
    """
    interfaces_data: dict[str, CANInterfaceStats] = {}

    # Handle non-Linux platforms or missing pyroute2
    if not CAN_SUPPORTED or IPRoute is None:
        platform_name = platform.system()
        msg = f"CAN bus not supported on {platform_name} platform - pyroute2 requires Linux"
        logger.debug(msg)
        # Return a placeholder entry so the UI has something to display
        for iface in buses:
            interfaces_data[iface] = CANInterfaceStats(
                name=iface, state="Listening (no pyroute2)", notes=msg
            )
        if not interfaces_data:
            interfaces_data["dummy_interface"] = CANInterfaceStats(
                name="dummy_interface", state=f"Unsupported/{platform_name}", notes=msg
            )
        return AllCANStats(interfaces=interfaces_data)

    # Linux platform with pyroute2 available
    try:
        pyroute2_stats = {}
        with IPRoute() as ipr:
            can_links = ipr.get_links(kind="can")
            for link in can_links:
                interface_name = link.get_attr("IFLA_IFNAME")
                try:
                    parsed_stats = get_stats_from_pyroute2_link(link)
                    pyroute2_stats[interface_name] = parsed_stats
                except Exception as e:
                    logger.exception(
                        f"Exception processing interface {interface_name} with pyroute2: {e}"
                    )
                    pyroute2_stats[interface_name] = CANInterfaceStats(
                        name=interface_name, state="Exception/Pyroute2Error"
                    )
        # Merge: for every interface the service is listening on, prefer pyroute2 stats if available
        for iface in buses:
            if iface in pyroute2_stats:
                interfaces_data[iface] = pyroute2_stats[iface]
                interfaces_data[iface].notes = (interfaces_data[iface].notes or "") + " (listening)"
            else:
                interfaces_data[iface] = CANInterfaceStats(
                    name=iface,
                    state="Listening",
                    notes="Interface in use by rvc2api, not found by pyroute2",
                )
        # Optionally, also report pyroute2 CAN interfaces not in buses (for diagnostics)
        for iface in pyroute2_stats:
            if iface not in interfaces_data:
                interfaces_data[iface] = pyroute2_stats[iface]
                interfaces_data[iface].notes = (
                    interfaces_data[iface].notes or ""
                ) + " (not in use by rvc2api)"
        if not interfaces_data and can_links:
            logger.warning(
                "CAN interfaces found but failed to retrieve status for all using pyroute2."
            )
            for link_obj in can_links:
                ifname = link_obj.get_attr("IFLA_IFNAME")
                if ifname not in interfaces_data:
                    interfaces_data[ifname] = CANInterfaceStats(
                        name=ifname, state="Error/ParseFailure"
                    )
    except Exception as e:
        logger.error(f"Failed to get CAN status using pyroute2: {e}", exc_info=True)
        return AllCANStats(interfaces={})

    return AllCANStats(interfaces=interfaces_data)


@api_router_can.get("/queue", response_model=dict[str, Any])
async def get_queue_status():
    """
    Return the current status of the CAN transmit queue.

    Provides the current number of items in the `can_tx_queue` and its
    maximum configured size.

    Returns:
        A dictionary with "length" (current queue size) and "maxsize"
        (maximum queue size, or "unbounded").
    """
    return {"length": can_tx_queue.qsize(), "maxsize": can_tx_queue.maxsize or "unbounded"}


@api_router_can.get("/can-sniffer", response_class=JSONResponse)
async def get_can_sniffer():
    """
    Returns the latest CAN messages (RX and TX, all types, deduplicated by source/PGN/instance).
    """
    from core_daemon.app_state import get_can_sniffer_log

    # Optionally deduplicate: only show the latest message for each
    # (arbitration_id, direction, instance)
    log = get_can_sniffer_log()
    seen = set()
    deduped = []
    for entry in reversed(log):
        key = (
            entry.get("arbitration_id"),
            entry.get("direction"),
            entry.get("instance"),
        )
        if key not in seen:
            deduped.append(entry)
            seen.add(key)
    return list(reversed(deduped))


@api_router_can.get("/can-sniffer-control", response_class=JSONResponse)
async def get_can_sniffer_control():
    """Returns grouped CAN command/control sniffer pairs with confidence (legacy view)."""
    return get_can_sniffer_grouped()


@api_router_can.get("/can-sniffer-log-debug", response_class=JSONResponse)
async def get_can_sniffer_log_debug():
    """
    Returns the last 20 entries in the raw CAN sniffer log for debugging.
    """
    from core_daemon.app_state import get_can_sniffer_log

    log = get_can_sniffer_log()
    return log[-20:]


@api_router_can.get("/network-map", response_class=JSONResponse)
async def get_network_map():
    """Returns all observed CAN source addresses, with decoded info if available."""
    from core_daemon.app_state import (
        device_lookup,
        get_controller_source_addr,  # Import the getter
        get_observed_source_addresses,
        last_seen_by_source_addr,
        status_lookup,
    )

    self_source_addr = get_controller_source_addr()  # Use global/configurable value
    addresses = get_observed_source_addresses()
    result = []
    for addr in addresses:
        entry = last_seen_by_source_addr.get(addr)
        dgn = entry.get("dgn_hex") if entry else None
        instance = (
            str(entry.get("instance")) if entry and entry.get("instance") is not None else None
        )
        # Try to find a friendly name from device_lookup or status_lookup
        friendly_name = None
        area = None
        device_type = None
        notes = None
        if dgn and instance:
            key = (dgn.upper(), instance)
            dev = status_lookup.get(key) or device_lookup.get(key)
            if dev:
                friendly_name = dev.get("friendly_name")
                area = dev.get("suggested_area")
                device_type = dev.get("device_type")
                notes = dev.get("notes")
        # Add all extra fields from the last-seen entry (decoded, raw, etc.)
        extra_fields = {}
        if entry:
            for k, v in entry.items():
                if k not in ("dgn_hex", "instance", "source_addr"):
                    extra_fields[k] = v
        result.append(
            {
                "value": addr,
                "is_self": addr == self_source_addr,
                "dgn": dgn,
                "instance": instance,
                "device_type": device_type,
                "friendly_name": friendly_name,
                "area": area,
                "notes": notes,
                **extra_fields,
            }
        )
    return result


# Utilities (formerly Troubleshooting)
@api_router_can.post("/canbus-scan", status_code=202)
async def start_canbus_scan(background_tasks: BackgroundTasks):
    """
    Initiates a CANbus scan (PGN 59904 requests for Address Claimed, Product ID,
    and Software Version). Results will be streamed to clients via WebSocket.
    """
    logger.info("CANbus scan requested via API endpoint.")
    background_tasks.add_task(run_canbus_scan_and_broadcast)
    return {"status": "scan started"}


# Implement the scan logic (skeleton)
async def run_canbus_scan_and_broadcast():
    """
    For each address (0x00-0xF9), send PGN 59904 requests for Address Claimed (0xEE00),
    Product ID (0xFEFA), and Software Version (0xFEFC) to all CAN interfaces.
    Listen for responses and broadcast them to WebSocket clients.
    """
    import time

    import can

    from core_daemon.app_state import get_controller_source_addr
    from core_daemon.can_manager import buses, can_tx_queue

    # PGNs to request
    pgns = [0xEE00, 0xFEFA, 0xFEFC]
    # PGN 59904 (Request)
    request_pgn = 0x00EA00
    # Get all available CAN interfaces
    interfaces = list(buses.keys())
    if not interfaces:
        logger.warning("No CAN interfaces available for CANbus scan.")
        return
    # Send requests to all addresses, including broadcast (0xFF)
    for dest_addr in [*range(0x00, 0xFA), 0xFF]:
        for pgn in pgns:
            # Compose 3-byte PGN in little-endian order for data field
            pgn_bytes = pgn.to_bytes(3, "little")
            data = pgn_bytes + bytes([0xFF, 0xFF, 0xFF, 0xFF, 0xFF])
            # Compose arbitration ID for PGN 59904 (Request)
            prio = 6
            dp = (request_pgn >> 16) & 1
            pf = (request_pgn >> 8) & 0xFF
            ps = dest_addr
            sa = get_controller_source_addr()
            arbitration_id = (prio << 26) | (dp << 24) | (pf << 16) | (ps << 8) | sa
            msg = can.Message(arbitration_id=arbitration_id, data=data, is_extended_id=True)
            for iface in interfaces:
                await can_tx_queue.put((msg, iface))
            await asyncio.sleep(0.002)  # Small delay to avoid CAN buffer overflow
    logger.info("CANbus scan requests sent. Listening for responses...")
    # Listen for responses for a short period (e.g., 2 seconds)
    start_time = time.time()
    seen_addresses = set()
    from core_daemon.app_state import last_seen_by_source_addr

    while time.time() - start_time < 2.0:
        # Check for new responses in last_seen_by_source_addr
        for addr, entry in last_seen_by_source_addr.items():
            if addr not in seen_addresses:
                seen_addresses.add(addr)
                # Broadcast the entry as a scan result
                await broadcast_canbus_scan_result(entry)
        await asyncio.sleep(0.1)
    logger.info("CANbus scan complete.")


api_router_can.add_api_websocket_route("/ws/network-map", network_map_ws_endpoint)
