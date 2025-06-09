"""
Device Discovery Feature

Integrates device discovery and polling capabilities into the feature management system.
Provides network topology mapping, device availability tracking, and active polling.
"""

import logging
from typing import Any

from backend.core.config import get_settings
from backend.services.device_discovery_service import DeviceDiscoveryService, DeviceInfo
from backend.services.feature_base import Feature

logger = logging.getLogger(__name__)


class DeviceDiscoveryFeature(Feature):
    """
    Feature for device discovery and network topology mapping.

    This feature provides:
    - Active device polling via PGN Request messages
    - Network topology discovery and mapping
    - Device availability tracking
    - Response time monitoring
    - Integration with WebSocket for real-time updates
    """

    def __init__(
        self,
        name: str,
        enabled: bool = False,
        core: bool = False,
        config: dict[str, Any] | None = None,
        dependencies: list[str] | None = None,
        friendly_name: str | None = None,
    ):
        """
        Initialize the device discovery feature.

        Args:
            name: Feature name
            enabled: Whether feature is enabled
            core: Whether this is a core feature
            config: Feature configuration
            dependencies: Feature dependencies
            friendly_name: Human-readable name
        """
        super().__init__(
            name=name,
            enabled=enabled,
            core=core,
            config=config or {},
            dependencies=dependencies or [],
            friendly_name=friendly_name,
        )

        self.settings = get_settings()

        # Service instance
        self.discovery_service: DeviceDiscoveryService | None = None

        # Integration state
        self._message_handler_registered = False
        self._websocket_updates_enabled = self.config.get("enable_websocket_updates", True)

        logger.info(f"DeviceDiscoveryFeature initialized (enabled: {self.enabled})")

    async def startup(self) -> None:
        """
        Initialize and start the device discovery feature.
        """
        if not self.enabled:
            logger.info("Device discovery feature is disabled")
            return

        try:
            # Initialize discovery service
            self.discovery_service = DeviceDiscoveryService(config=self.settings)

            # Start discovery service
            await self.discovery_service.start_discovery()

            logger.info("Device discovery feature started successfully")

        except Exception as e:
            logger.error(f"Failed to start device discovery feature: {e}", exc_info=True)
            raise

    async def shutdown(self) -> None:
        """
        Stop the device discovery feature.
        """
        if not self.discovery_service:
            return

        try:
            await self.discovery_service.stop_discovery()
            logger.info("Device discovery feature stopped")

        except Exception as e:
            logger.error(f"Failed to stop device discovery feature: {e}", exc_info=True)
            raise

    @property
    def health(self) -> str:
        """
        Get the health status of the device discovery feature.

        Returns:
            Health status string
        """
        if not self.enabled:
            return "healthy"  # Disabled features are considered healthy

        if not self.discovery_service:
            return "failed"  # Service not initialized

        # Check if discovery is active
        if hasattr(self.discovery_service, "discovery_active"):
            return "healthy" if self.discovery_service.discovery_active else "degraded"

        return "healthy"

    async def health_check(self) -> dict[str, Any]:
        """
        Perform health check for the device discovery feature.

        Returns:
            Dictionary containing health status information
        """
        if not self.enabled:
            return {
                "status": "disabled",
                "message": "Device discovery feature is disabled",
            }

        if not self.discovery_service:
            return {"status": "error", "message": "Discovery service not initialized"}

        try:
            # Get service status
            topology = await self.discovery_service.get_network_topology()
            availability = await self.discovery_service.get_device_availability()

            status = "healthy"
            message = "Device discovery operating normally"

            # Check for potential issues
            if topology.get("total_devices", 0) == 0:
                status = "warning"
                message = "No devices discovered yet"
            elif (
                availability.get("online_devices", 0) / max(availability.get("total_devices", 1), 1)
                < 0.5
            ):
                status = "warning"
                message = "Low device availability detected"

            return {
                "status": status,
                "message": message,
                "metrics": {
                    "discovery_active": topology.get("discovery_active", False),
                    "total_devices": topology.get("total_devices", 0),
                    "online_devices": availability.get("online_devices", 0),
                    "active_polls": topology.get("active_polls", 0),
                    "last_discovery": topology.get("last_discovery", 0),
                },
            }

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"status": "error", "message": f"Health check failed: {e!s}"}

    async def get_feature_info(self) -> dict[str, Any]:
        """
        Get feature information and status.

        Returns:
            Dictionary containing feature information
        """
        info = {
            "name": "device_discovery",
            "friendly_name": "Device Discovery & Polling",
            "description": "Active device polling and network discovery for CAN bus systems",
            "enabled": self.enabled,
            "version": "1.0.0",
        }

        if self.discovery_service:
            # Add runtime information
            topology = await self.discovery_service.get_network_topology()
            info.update(
                {
                    "runtime_info": {
                        "discovery_active": topology.get("discovery_active", False),
                        "total_devices": topology.get("total_devices", 0),
                        "supported_protocols": self.config.get("supported_protocols", []),
                        "polling_interval": self.config.get("polling_interval_seconds", 30),
                        "discovery_interval": self.config.get("discovery_interval_seconds", 300),
                    }
                }
            )

        return info

    # Public API methods for other features to use

    async def discover_devices(self, protocol: str = "rvc") -> dict[int, DeviceInfo]:
        """
        Perform device discovery for a specific protocol.

        Args:
            protocol: Protocol to use for discovery

        Returns:
            Dictionary of discovered devices
        """
        if not self.discovery_service:
            return {}

        return await self.discovery_service.discover_devices(protocol)

    async def poll_device(
        self,
        source_address: int,
        pgn: int,
        protocol: str = "rvc",
        instance: int | None = None,
    ) -> bool:
        """
        Poll a specific device for status.

        Args:
            source_address: Target device address
            pgn: PGN to request
            protocol: Protocol to use
            instance: Instance number if applicable

        Returns:
            True if poll was initiated successfully
        """
        if not self.discovery_service:
            return False

        return await self.discovery_service.poll_device(
            source_address=source_address, pgn=pgn, protocol=protocol, instance=instance
        )

    async def get_network_topology(self) -> dict[str, Any]:
        """
        Get current network topology information.

        Returns:
            Dictionary containing topology data
        """
        if not self.discovery_service:
            return {}

        return await self.discovery_service.get_network_topology()

    async def get_device_availability(self) -> dict[str, Any]:
        """
        Get device availability statistics.

        Returns:
            Dictionary containing availability metrics
        """
        if not self.discovery_service:
            return {}

        return await self.discovery_service.get_device_availability()

    # Private methods

    def _process_can_message(self, message) -> None:
        """
        Process incoming CAN messages for device discovery.

        Args:
            message: CAN message to process
        """
        if self.discovery_service:
            self.discovery_service.process_can_message(message)
            logger.debug("Processed CAN message for device discovery")
