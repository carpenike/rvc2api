"""
CAN Bus API Router

FastAPI router for CAN bus operations and monitoring.
This router delegates business logic to the CANService.

Routes:
- GET /can/queue/status: Get CAN transmission queue status
- GET /can/interfaces: Get list of active CAN interfaces
- GET /can/interfaces/details: Get detailed interface information
- GET /can/status: Get detailed CAN interface status with pyroute2 stats
- POST /can/send: Send raw CAN message
- GET /can/statistics: Get CAN bus statistics
- WebSocket /ws/can/scan: Real-time CAN scan results
"""

import logging
import platform
from typing import Annotated, Any

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect,
)

from backend.core.dependencies import get_can_service, get_feature_manager_from_request

# Import buses from the old structure for compatibility
from backend.integrations.can.manager import buses

# Import models from the new backend structure
from backend.models.can import AllCANStats, CANInterfaceStats

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

# Create the router
router = APIRouter(prefix="/api/can", tags=["can"])

# WebSocket clients for CAN scan results
canbus_scan_ws_clients: set[WebSocket] = set()


def _check_can_interface_feature_enabled(request: Request) -> None:
    """Check if can_interface feature is enabled, raise 404 if disabled."""
    feature_manager = get_feature_manager_from_request(request)
    if not feature_manager.is_enabled("can_interface"):
        raise HTTPException(status_code=404, detail="can_interface feature is disabled")


@router.get(
    "/queue/status",
    response_model=dict[str, Any],
    summary="Get CAN queue status",
    description="Return the current status of the CAN transmission queue.",
    response_description="Queue status including length and capacity information",
)
async def get_queue_status(
    request: Request,
    can_service: Annotated[Any, Depends(get_can_service)],
) -> dict[str, Any]:
    """
    Return the current status of the CAN transmission queue.

    This endpoint provides information about pending CAN messages
    waiting to be transmitted.
    """
    logger.debug("GET /can/queue/status - Retrieving CAN queue status")
    _check_can_interface_feature_enabled(request)

    try:
        status = await can_service.get_queue_status()
        queue_length = status.get("queue_length", 0)
        logger.info(f"Retrieved CAN queue status: {queue_length} messages pending")
        return status
    except Exception as e:
        logger.error(f"Error retrieving CAN queue status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.get(
    "/interfaces",
    response_model=list[str],
    summary="Get CAN interfaces",
    description="Return a list of active CAN interfaces.",
    response_description="List of interface names",
)
async def get_interfaces(
    request: Request,
    can_service: Annotated[Any, Depends(get_can_service)],
) -> list[str]:
    """
    Return a list of active CAN interfaces.

    This endpoint provides information about currently available
    CAN bus interfaces in the system.
    """
    logger.debug("GET /can/interfaces - Retrieving CAN interfaces")
    _check_can_interface_feature_enabled(request)

    try:
        interfaces = await can_service.get_interfaces()
        logger.info(f"Retrieved {len(interfaces)} CAN interfaces: {', '.join(interfaces)}")
        return interfaces
    except Exception as e:
        logger.error(f"Error retrieving CAN interfaces: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.get(
    "/interfaces/details",
    response_model=dict[str, dict[str, Any]],
    summary="Get detailed interface information",
    description="Return detailed information about all CAN interfaces.",
    response_description="Dictionary mapping interface names to their details",
)
async def get_interface_details(
    request: Request,
    can_service: Annotated[Any, Depends(get_can_service)],
) -> dict[str, dict[str, Any]]:
    """
    Return detailed information about all CAN interfaces.

    This endpoint provides comprehensive information about each
    CAN interface including status, statistics, and configuration.
    """
    logger.debug("GET /can/interfaces/details - Retrieving detailed interface information")
    _check_can_interface_feature_enabled(request)

    try:
        details = await can_service.get_interface_details()
        interface_count = len(details)
        logger.info(f"Retrieved detailed information for {interface_count} CAN interfaces")
        return details
    except Exception as e:
        logger.error(f"Error retrieving CAN interface details: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.post(
    "/send",
    response_model=dict[str, Any],
    summary="Send raw CAN message",
    description="Send a raw CAN message to the specified interface.",
    response_description="Send operation result",
)
async def send_raw_message(
    request: Request,
    arbitration_id: int,
    data: str,
    interface: str,
    can_service: Annotated[Any, Depends(get_can_service)],
) -> dict[str, Any]:
    """
    Send a raw CAN message to the specified interface.

    Args:
        arbitration_id: CAN arbitration ID (hex or decimal)
        data: Hex string data payload (e.g., "01020304")
        interface: Target CAN interface name

    Returns:
        Dictionary with send status and details

    Raises:
        HTTPException: If parameters are invalid or send fails
    """
    logger.info(
        f"POST /can/send - Sending CAN message: ID=0x{arbitration_id:X}, data='{data}', interface='{interface}'"
    )
    _check_can_interface_feature_enabled(request)

    # Convert hex string to bytes
    try:
        data_bytes = bytes.fromhex(data.replace(" ", "").replace("0x", ""))
        logger.debug(f"Converted hex data '{data}' to {len(data_bytes)} bytes")
    except ValueError as e:
        logger.warning(f"Invalid hex data provided: '{data}' - {e}")
        raise HTTPException(status_code=400, detail=f"Invalid hex data: {e}") from e

    try:
        result = await can_service.send_raw_message(arbitration_id, data_bytes, interface)
        if result.get("success", False):
            logger.info(
                f"Successfully sent CAN message: ID=0x{arbitration_id:X} on interface '{interface}'"
            )
        else:
            logger.warning(
                f"Failed to send CAN message: ID=0x{arbitration_id:X} on interface '{interface}' - {result.get('error', 'Unknown error')}"
            )
        return result
    except Exception as e:
        logger.error(
            f"Error sending CAN message: ID=0x{arbitration_id:X} on interface '{interface}': {e}",
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.get(
    "/recent",
    response_model=list[dict[str, Any]],
    summary="Get recent CAN messages",
    description="Return recent CAN messages captured on the bus.",
    response_description="List of recent CAN messages with metadata",
)
async def get_recent_can_messages(
    request: Request,
    can_service: Annotated[Any, Depends(get_can_service)],
    limit: int = 100,
) -> list[dict[str, Any]]:
    """
    Return recent CAN messages captured on the bus.

    Args:
        limit: Maximum number of messages to return (default: 100)

    Returns:
        List of recent CAN messages with decoded information

    Raises:
        HTTPException: 503 if CAN interfaces are not available or connected
    """
    logger.debug(f"GET /can/recent - Retrieving recent CAN messages (limit={limit})")
    _check_can_interface_feature_enabled(request)

    try:
        messages = await can_service.get_recent_messages(limit)
        logger.info(f"Retrieved {len(messages)} recent CAN messages")
        return messages
    except ConnectionError as e:
        logger.error(f"Failed to connect to CAN bus interface: {e}")
        raise HTTPException(
            status_code=503, detail=f"Failed to connect to CAN bus interface: {e!s}"
        ) from e
    except Exception as e:
        logger.error(f"Error retrieving recent CAN messages: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.get(
    "/statistics",
    response_model=dict[str, Any],
    summary="Get CAN bus statistics",
    description="Return statistics for all CAN bus interfaces.",
    response_description="Dictionary containing bus statistics and metrics",
)
async def get_bus_statistics(
    request: Request,
    can_service: Annotated[Any, Depends(get_can_service)],
) -> dict[str, Any]:
    """
    Return statistics for all CAN bus interfaces.

    This endpoint provides metrics and statistics about CAN bus
    performance, message counts, and error rates.
    """
    logger.debug("GET /can/statistics - Retrieving CAN bus statistics")
    _check_can_interface_feature_enabled(request)

    try:
        statistics = await can_service.get_bus_statistics()

        # Log summary of statistics
        interface_count = len(statistics.get("interfaces", {}))
        total_messages = sum(
            iface_stats.get("message_count", 0)
            for iface_stats in statistics.get("interfaces", {}).values()
        )
        logger.info(
            f"Retrieved CAN bus statistics: {interface_count} interfaces, {total_messages} total messages"
        )
        return statistics
    except Exception as e:
        logger.error(f"Error retrieving CAN bus statistics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.websocket("/ws/scan")
async def canbus_scan_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time CAN bus scan results.

    This endpoint provides a live stream of CAN bus activity,
    including message parsing, device discovery, and network mapping.
    """
    await websocket.accept()
    canbus_scan_ws_clients.add(websocket)

    logger.info("CAN scan WebSocket client connected")

    try:
        while True:
            # Keep the connection open
            # Scan results will be pushed from background tasks
            await websocket.receive_text()
    except WebSocketDisconnect:
        canbus_scan_ws_clients.discard(websocket)
        logger.info("CAN scan WebSocket client disconnected")


async def broadcast_scan_result(scan_data: dict[str, Any]) -> None:
    """
    Broadcast scan results to all connected WebSocket clients.

    Args:
        scan_data: Dictionary containing scan results to broadcast
    """
    if not canbus_scan_ws_clients:
        return

    disconnected_clients = set()

    for client in canbus_scan_ws_clients:
        try:
            await client.send_json(scan_data)
        except Exception as e:
            logger.warning(f"Failed to send scan data to client: {e}")
            disconnected_clients.add(client)

    # Clean up disconnected clients
    for client in disconnected_clients:
        canbus_scan_ws_clients.discard(client)


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

    # CAN specific details are often in IFLA_LINKINFO -> INFO_DATA
    linkinfo = link.get("linkinfo")
    if linkinfo and linkinfo.get_attr("IFLA_INFO_KIND") == "can":
        info_data = linkinfo.get("info_data")
        if info_data:
            stats.bitrate = info_data.get_attr("CAN_BITTIMING_BITRATE")
            # sample_point is often in permille (1/1000)
            sample_point = info_data.get_attr("CAN_BITTIMING_SAMPLE_POINT")
            if sample_point is not None:
                stats.sample_point = sample_point / 1000.0

            # CAN state (ERROR-ACTIVE, ERROR-WARNING, ERROR-PASSIVE, BUS-OFF)
            can_state_val = info_data.get_attr("CAN_STATE")
            if can_state_val is not None:
                # pyroute2 provides integer constants for these states
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

    # Additional interface details
    stats.promiscuity = link.get_attr("IFLA_PROMISCUITY")

    return stats


@router.get("/status", response_model=AllCANStats)
async def get_can_status(
    request: Request,
    can_service: Annotated[Any, Depends(get_can_service)],
) -> AllCANStats:
    """
    Retrieves detailed status for all CAN interfaces the service is listening on.
    Combines pyroute2 stats (if available) with the actual set of active interfaces.
    On non-Linux platforms, returns a platform-specific message.
    """
    logger.debug("GET /can/status - Retrieving detailed CAN status")
    _check_can_interface_feature_enabled(request)

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
        logger.info(
            f"Retrieved CAN status for {platform_name} platform: {len(interfaces_data)} interfaces (no pyroute2)"
        )
        return AllCANStats(interfaces=interfaces_data)

    # Linux platform with pyroute2 available
    try:
        pyroute2_stats = {}
        with IPRoute() as ipr:
            can_links = ipr.get_links(kind="can")
            logger.debug(f"Found {len(can_links)} CAN links via pyroute2")
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

        logger.info(f"Retrieved detailed CAN status: {len(interfaces_data)} interfaces")
        return AllCANStats(interfaces=interfaces_data)

    except Exception as e:
        logger.error(f"Failed to get CAN status using pyroute2: {e}", exc_info=True)
        return AllCANStats(interfaces={})
