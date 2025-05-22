"""
CAN bus feature for the new architecture.

This module provides a Feature-based implementation for CAN bus integration,
listening to CAN messages and integrating with the event system.
"""

import asyncio
import contextlib
import logging
import time
from typing import Any

from backend.core.events import get_event_bus
from backend.services.feature_base import Feature

logger = logging.getLogger(__name__)


class CANBusFeature(Feature):
    """
    Feature for CAN bus integration.

    This feature manages CAN bus interfaces, listening for messages and
    processing them according to the configured decoders.
    """

    def __init__(
        self,
        name: str = "can_bus",
        enabled: bool = True,
        core: bool = True,
        config: dict[str, Any] | None = None,
        dependencies: list[str] | None = None,
    ) -> None:
        """
        Initialize the CAN bus feature.

        Args:
            name: Feature name (default: "can_bus")
            enabled: Whether the feature is enabled (default: True)
            core: Whether this is a core feature (default: True)
            config: Configuration options (default: None)
            dependencies: Feature dependencies (default: ["app_state"])
        """
        # Ensure we depend on app_state
        deps = dependencies or []
        if "app_state" not in deps:
            deps.append("app_state")

        # Initialize with provided config or defaults
        config_dict = config or {}
        self.config = {
            "interfaces": config_dict.get("interfaces", ["vcan0"]),
            "bustype": config_dict.get("bustype", "socketcan"),
            "bitrate": config_dict.get("bitrate", 250000),
            "poll_interval": config_dict.get("poll_interval", 0.1),  # seconds
            "simulate": config_dict.get("simulate", False),
        }

        super().__init__(
            name=name,
            enabled=enabled,
            core=core,
            config=self.config,
            dependencies=deps,
        )

        # CAN bus related attributes
        self._listeners: list[Any] = []  # Will store CAN listeners or notifiers
        self._writer_task: asyncio.Task | None = None
        self._message_queue: asyncio.Queue = asyncio.Queue()

        # State
        self._is_running = False
        self._task: asyncio.Task | None = None
        self._simulation_task: asyncio.Task | None = None

    async def startup(self) -> None:
        """
        Start CAN bus listeners and message processing.

        This method is called automatically by the FeatureManager.
        """
        logger.info("Starting CAN bus feature")

        if self.config["simulate"]:
            # Start simulation mode
            logger.info("Starting CAN bus simulation mode")
            self._simulation_task = asyncio.create_task(self._simulate_can_messages())
        else:
            # Start real CAN bus listeners
            try:
                # Here we would import python-can and set up real listeners
                # This is placeholder code that would be replaced with actual implementation
                interfaces = self.config["interfaces"]
                bustype = self.config["bustype"]
                bitrate = self.config["bitrate"]

                logger.info(
                    f"Setting up CAN bus listeners: interfaces={interfaces}, "
                    f"bustype={bustype}, bitrate={bitrate}"
                )

                # Setup would involve creating python-can Bus objects and listeners
                # self._listeners = []
                # for interface in interfaces:
                #     bus = can.Bus(interface=interface, bustype=bustype, bitrate=bitrate)
                #     listener = can.Notifier(bus, [self._process_message])
                #     self._listeners.append((bus, listener))

                # Start the message writer task
                self._writer_task = asyncio.create_task(self._message_writer_loop())

            except ImportError:
                logger.warning(
                    "python-can package not available. CAN bus feature will not start. "
                    "Install with 'poetry add python-can'."
                )
                # Fall back to simulation mode
                logger.info("Falling back to CAN bus simulation mode")
                self._simulation_task = asyncio.create_task(self._simulate_can_messages())
            except Exception as e:
                logger.error(f"Failed to start CAN bus listeners: {e}", exc_info=True)
                return

        self._is_running = True

    async def shutdown(self) -> None:
        """
        Shutdown CAN bus listeners and clean up resources.

        This method is called automatically by the FeatureManager.
        """
        logger.info("Shutting down CAN bus feature")

        self._is_running = False

        # Cancel simulation task if running
        if self._simulation_task:
            self._simulation_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._simulation_task

        # Cancel writer task if running
        if self._writer_task:
            self._writer_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._writer_task

        # Cleanup CAN bus listeners
        for _listener in self._listeners:
            try:
                # Depending on how listeners were set up, cleanup might involve:
                # - Stopping notifiers
                # - Closing bus connections
                # - Releasing resources
                pass
            except Exception as e:
                logger.error(f"Error cleaning up CAN listener: {e}")

        self._listeners = []

    @property
    def health(self) -> str:
        """Return the health status of the feature."""
        if not self.enabled:
            return "disabled"

        if self._is_running:
            # In a real implementation, we might check connection status to CAN interfaces
            if self.config["simulate"]:
                return "healthy (simulation mode)"
            return "healthy"

        return "unhealthy"

    async def send_message(
        self, arbitration_id: int, data: bytes, extended_id: bool = True
    ) -> bool:
        """
        Send a CAN message to the bus.

        Args:
            arbitration_id: The arbitration ID for the message
            data: The message data as bytes
            extended_id: Whether to use extended ID format

        Returns:
            Boolean indicating success
        """
        if not self._is_running:
            logger.warning("Cannot send CAN message: feature is not running")
            return False

        # In simulation mode, just log the message
        if self.config["simulate"]:
            logger.info(
                f"SIMULATION - Sending CAN message: "
                f"id=0x{arbitration_id:x}, data={data.hex()}, extended_id={extended_id}"
            )
            return True

        # In real mode, queue the message for sending
        try:
            # Create a message dict
            message = {
                "arbitration_id": arbitration_id,
                "data": data,
                "extended_id": extended_id,
                "timestamp": time.time(),
            }

            # Queue the message
            await self._message_queue.put(message)
            return True
        except Exception as e:
            logger.error(f"Error queuing CAN message for sending: {e}")
            return False

    async def _process_message(self, msg: dict[str, Any]) -> None:
        """
        Process an incoming CAN message.

        This method would be called by the CAN bus listener when a message is received.
        It processes the message and publishes events as needed.

        Args:
            msg: The CAN message as a dictionary with keys like arbitration_id, data, etc.
        """
        event_bus = get_event_bus()
        if not event_bus:
            return

        try:
            # Extract message data
            arbitration_id = msg.get("arbitration_id")
            data = msg.get("data")
            timestamp = msg.get("timestamp", time.time())

            if arbitration_id is None or data is None:
                logger.warning("Received invalid CAN message")
                return

            # Log the message at debug level
            logger.debug(
                f"CAN message received: "
                f"id=0x{arbitration_id:x}, data={data.hex() if isinstance(data, bytes) else data}"
            )

            # Publish raw CAN message event
            event_bus.publish(
                "can_message_received",
                {
                    "arbitration_id": arbitration_id,
                    "data": data.hex() if isinstance(data, bytes) else data,
                    "timestamp": timestamp,
                },
            )

            # Here we could add additional processing, like:
            # - Decoding the message using RV-C decoders
            # - Updating entity states based on the decoded message
            # - Publishing more specific events

        except Exception as e:
            logger.error(f"Error processing CAN message: {e}")

    async def _message_writer_loop(self) -> None:
        """
        Background task to process and send queued CAN messages.
        """
        logger.info("Starting CAN message writer loop")

        while self._is_running:
            try:
                # Get the next message from the queue
                message = await self._message_queue.get()

                # Send the message to all configured interfaces
                sent = False
                for _listener in self._listeners:
                    try:
                        # In a real implementation, we'd send to the bus
                        # bus = listener[0]  # Assuming first item is the bus
                        # message = can.Message(
                        #     arbitration_id=message["arbitration_id"],
                        #     data=message["data"],
                        #     extended_id=message["extended_id"],
                        # )
                        # bus.send(message)
                        sent = True
                    except Exception as e:
                        logger.error(f"Failed to send CAN message: {e}")

                if sent:
                    logger.debug(
                        f"Sent CAN message: "
                        f"id=0x{message['arbitration_id']:x}, "
                        f"data={message['data'].hex() if isinstance(message['data'], bytes) else message['data']}"
                    )

                # Mark the task as done
                self._message_queue.task_done()

            except asyncio.CancelledError:
                logger.info("CAN message writer loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in CAN message writer loop: {e}")
                await asyncio.sleep(1)  # Avoid tight loop on persistent errors

    async def _simulate_can_messages(self) -> None:
        """
        Simulate CAN messages for testing purposes.

        This method generates simulated CAN messages at regular intervals.
        """
        logger.info("Starting CAN message simulation")

        # Counter for cycling through different message types
        counter = 0

        while self._is_running:
            try:
                await asyncio.sleep(1.0)  # 1 message per second

                # Generate a simulated message based on the counter
                msg_type = counter % 4

                if msg_type == 0:
                    # Simulate a temperature message (DGN 1FEA5 / 130725)
                    arbitration_id = 0x1FEA5
                    # Temperature of 72.5°F (22.5°C)
                    data = bytes([0x02, 0x01, 0x00, 0x00, 0xE1, 0x01, 0x00, 0xFF])
                elif msg_type == 1:
                    # Simulate a battery state message (DGN 1FFFD / 131069)
                    arbitration_id = 0x1FFFD
                    # Battery at 80% charge
                    data = bytes([0x01, 0x50, 0x00, 0x00, 0x00, 0x00, 0xFF, 0xFF])
                elif msg_type == 2:
                    # Simulate a light status message (DGN 1FEED / 130797)
                    arbitration_id = 0x1FEED
                    # Light is on
                    data = bytes([0x01, 0x01, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF])
                else:
                    # Simulate a tank level message (DGN 1FF9D / 130973)
                    arbitration_id = 0x1FF9D
                    # Tank at 65% capacity
                    data = bytes([0x01, 0x41, 0x00, 0x00, 0x00, 0xFF, 0xFF, 0xFF])

                # Process the simulated message
                await self._process_message(
                    {
                        "arbitration_id": arbitration_id,
                        "data": data,
                        "extended_id": True,
                        "timestamp": time.time(),
                    }
                )

                counter += 1

            except asyncio.CancelledError:
                logger.info("CAN message simulation cancelled")
                break
            except Exception as e:
                logger.error(f"Error in CAN message simulation: {e}")
                await asyncio.sleep(5)  # Longer sleep on error


# Singleton instance and accessor functions
_can_bus_feature: CANBusFeature | None = None


def initialize_can_bus_feature(
    config: dict[str, Any] | None = None,
) -> CANBusFeature:
    """
    Initialize the CAN bus feature singleton.

    Args:
        config: Optional configuration dictionary

    Returns:
        The initialized CANBusFeature instance
    """
    global _can_bus_feature

    if _can_bus_feature is None:
        _can_bus_feature = CANBusFeature(
            config=config,
        )

    return _can_bus_feature


def get_can_bus_feature() -> CANBusFeature:
    """
    Get the CAN bus feature singleton instance.

    Returns:
        The CANBusFeature instance

    Raises:
        RuntimeError: If the CAN bus feature has not been initialized
    """
    if _can_bus_feature is None:
        raise RuntimeError(
            "CAN bus feature has not been initialized. Call initialize_can_bus_feature() first."
        )

    return _can_bus_feature
