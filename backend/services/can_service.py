"""
CAN Service

Handles business logic for CAN bus operations, including:
- CAN bus status and queue monitoring
- Raw CAN message sending
- CAN bus management
- Interface information retrieval

This service extracts CAN-related business logic from the API router layer.
"""

import asyncio
import logging
from typing import Any

import can

from backend.integrations.can.manager import buses, can_tx_queue

logger = logging.getLogger(__name__)


class CANService:
    """
    Service for managing CAN bus operations and monitoring.

    This service provides business logic for CAN operations while being
    agnostic to the presentation layer (HTTP, WebSocket, etc.).
    """

    def __init__(self, app_state=None):
        """
        Initialize the CAN service.

        Args:
            app_state: Optional AppState instance for dependency injection
        """
        self.app_state = app_state

    async def get_queue_status(self) -> dict[str, Any]:
        """
        Get the current status of the CAN transmission queue.

        Returns:
            dict: Dictionary containing queue length and max size information.
        """
        return {
            "length": can_tx_queue.qsize(),
            "maxsize": can_tx_queue.maxsize or "unbounded",
        }

    async def get_interfaces(self) -> list[str]:
        """
        Get a list of active CAN interfaces.

        Returns:
            list: List of interface names that are currently active.
        """
        return list(buses.keys())

    async def get_interface_details(self) -> dict[str, dict[str, Any]]:
        """
        Get detailed information about all CAN interfaces.

        Returns:
            dict: Dictionary mapping interface names to their details.
        """
        interface_details = {}

        for interface_name, bus in buses.items():
            try:
                details = {
                    "name": interface_name,
                    "channel": getattr(bus, "channel", "unknown"),
                    "bustype": getattr(bus, "bus_type", "unknown"),
                    "state": "active" if bus else "inactive",
                }

                # Add additional bus-specific information if available
                if hasattr(bus, "get_stats"):
                    try:
                        stats = bus.get_stats()  # type: ignore[attr-defined]
                        details["stats"] = stats
                    except Exception:
                        pass

                interface_details[interface_name] = details

            except Exception as e:
                logger.warning(f"Failed to get details for interface {interface_name}: {e}")
                interface_details[interface_name] = {
                    "name": interface_name,
                    "error": str(e),
                    "state": "error",
                }

        return interface_details

    async def send_raw_message(
        self, arbitration_id: int, data: bytes, interface: str
    ) -> dict[str, Any]:
        """
        Send a raw CAN message to the specified interface.

        Args:
            arbitration_id: CAN arbitration ID
            data: Raw message data
            interface: Target CAN interface name

        Returns:
            dict: Dictionary with send status and details.

        Raises:
            ValueError: If interface is invalid or message parameters are wrong.
        """
        # Validate arbitration ID
        if not (0 <= arbitration_id <= 0x1FFFFFFF):
            raise ValueError(f"Invalid arbitration ID: {arbitration_id}")

        # Validate data length
        if len(data) > 8:
            raise ValueError(f"CAN data too long: {len(data)} bytes (max 8)")

        # Validate interface exists
        if interface not in buses:
            available_interfaces = list(buses.keys())
            raise ValueError(
                f"Interface '{interface}' not found. Available interfaces: {available_interfaces}"
            )

        # Create CAN message
        msg = can.Message(
            arbitration_id=arbitration_id,
            data=data,
            is_extended_id=arbitration_id > 0x7FF,
        )

        try:
            # Queue the message for transmission
            await can_tx_queue.put((msg, interface))

            logger.info(
                f"Raw CAN message queued: ID=0x{arbitration_id:08X}, "
                f"data={data.hex().upper()}, interface={interface}"
            )

            return {
                "status": "queued",
                "arbitration_id": arbitration_id,
                "arbitration_id_hex": f"0x{arbitration_id:08X}",
                "data": data.hex().upper(),
                "interface": interface,
                "queue_size": can_tx_queue.qsize(),
            }

        except Exception as e:
            logger.error(f"Failed to queue raw CAN message: {e}")
            return {
                "status": "error",
                "error": str(e),
                "arbitration_id": arbitration_id,
                "arbitration_id_hex": f"0x{arbitration_id:08X}",
                "data": data.hex().upper(),
                "interface": interface,
            }

    async def get_bus_statistics(self) -> dict[str, Any]:
        """
        Get comprehensive statistics about CAN bus operations.

        Returns:
            dict: Dictionary containing bus statistics and metrics.
        """
        stats = {
            "interfaces": {},
            "queue": await self.get_queue_status(),
            "summary": {
                "total_interfaces": len(buses),
                "active_interfaces": len([b for b in buses.values() if b]),
                "queue_utilization": (
                    can_tx_queue.qsize() / can_tx_queue.maxsize if can_tx_queue.maxsize else 0
                ),
            },
        }

        # Get per-interface statistics
        for interface_name, bus in buses.items():
            interface_stats = {
                "name": interface_name,
                "active": bool(bus),
                "type": getattr(bus, "bus_type", "unknown") if bus else "unknown",
            }

            if bus:
                try:
                    # Try to get bus-specific statistics
                    if hasattr(bus, "get_stats"):
                        bus_stats = bus.get_stats()  # type: ignore[attr-defined]
                        interface_stats.update(bus_stats)
                except Exception as e:
                    interface_stats["stats_error"] = str(e)

            stats["interfaces"][interface_name] = interface_stats

        return stats

    async def start_can_writer(self) -> None:
        """
        Start the CAN writer task.

        This method would typically be called during application startup
        to begin the CAN message transmission loop.
        """
        if not self.app_state:
            logger.warning("Cannot start CAN writer without AppState dependency")
            return

        # Import here to avoid circular imports
        from backend.integrations.can.manager import can_writer

        # Start the CAN writer task and store reference to prevent garbage collection
        can_writer_task = asyncio.create_task(can_writer(self.app_state))
        self._can_writer_task = can_writer_task
        logger.info("CAN writer task started")

    async def shutdown(self) -> None:
        """
        Shutdown the CAN service and clean up background tasks.

        This method cancels and awaits the CAN writer task to ensure
        graceful shutdown without hanging background tasks.
        """
        logger.info("Shutting down CANService")

        # Cancel and await the CAN writer task if it exists
        if hasattr(self, "_can_writer_task") and self._can_writer_task:
            logger.info("Cancelling CAN writer task")
            self._can_writer_task.cancel()
            try:
                await self._can_writer_task
            except asyncio.CancelledError:
                logger.info("CAN writer task cancelled successfully")
            except Exception as e:
                logger.error(f"Error during CAN writer task cancellation: {e}")

        logger.info("CANService shutdown complete")

    async def send_message(
        self, arbitration_id: int, data: bytes, interface: str
    ) -> dict[str, Any]:
        """
        Send a CAN message (alias for send_raw_message for compatibility).

        Args:
            arbitration_id: CAN arbitration ID
            data: Raw message data
            interface: Target CAN interface name

        Returns:
            dict: Dictionary with send status and details.
        """
        return await self.send_raw_message(arbitration_id, data, interface)

    async def get_recent_messages(self, limit: int = 100) -> list[dict[str, Any]]:
        """
        Get recent CAN messages captured on the bus.

        Args:
            limit: Maximum number of messages to return (default: 100)

        Returns:
            list: List of recent CAN messages with decoded information.
        """
        # This is a placeholder implementation. In a real system, this would
        # fetch messages from a message buffer or database.
        # For now, we return an empty list as no message storage is implemented.
        logger.debug(f"Requested {limit} recent CAN messages")

        # TODO: Implement actual message storage and retrieval
        # This could involve:
        # 1. Keeping a circular buffer of recent messages
        # 2. Storing messages in a database
        # 3. Reading from the CAN sniffer feature if available

        return []

    async def initialize_can_interfaces(
        self, interfaces: list[str] | None = None
    ) -> dict[str, Any]:
        """
        Initialize CAN interfaces.

        Args:
            interfaces: List of interface names to initialize

        Returns:
            dict: Dictionary with initialization status.
        """
        import os

        from can.exceptions import CanInterfaceNotImplementedError

        if interfaces is None:
            interfaces = []

        default_bustype = os.getenv("CAN_BUSTYPE", "socketcan")
        initialized = []
        failed = []

        for interface_name in interfaces:
            try:
                if interface_name not in buses:
                    bus = can.interface.Bus(channel=interface_name, bustype=default_bustype)
                    buses[interface_name] = bus
                    initialized.append(interface_name)
                    logger.info(f"Initialized CAN interface: {interface_name}")
                else:
                    logger.info(f"CAN interface already initialized: {interface_name}")
                    initialized.append(interface_name)
            except CanInterfaceNotImplementedError as e:
                logger.error(f"CAN interface '{interface_name}' not implemented: {e}")
                failed.append({"interface": interface_name, "error": str(e)})
            except Exception as e:
                logger.error(f"Failed to initialize CAN interface '{interface_name}': {e}")
                failed.append({"interface": interface_name, "error": str(e)})

        return {
            "initialized": initialized,
            "failed": failed,
            "total_interfaces": len(buses),
        }
