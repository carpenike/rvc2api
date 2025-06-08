"""
Multi-Network CAN Feature for RVC2API

Feature integration for the multi-network CAN manager, providing:
- Seamless integration with the feature management system
- Configuration-driven network setup
- Health monitoring and status reporting
- Graceful degradation when disabled
"""

import logging
from typing import Any

from backend.core.config import get_multi_network_settings
from backend.integrations.can.multi_network_manager import get_multi_network_manager
from backend.services.feature_base import Feature

logger = logging.getLogger(__name__)


class MultiNetworkCANFeature(Feature):
    """
    Multi-Network CAN Feature

    Integrates the multi-network CAN manager with the feature management system,
    providing configuration-driven network setup and health monitoring.
    """

    def __init__(
        self,
        name: str = "multi_network_can",
        enabled: bool = False,
        core: bool = False,
        config: dict[str, Any] | None = None,
        dependencies: list[str] | None = None,
        friendly_name: str | None = None,
    ):
        super().__init__(
            name=name,
            enabled=enabled,
            core=core,
            config=config,
            dependencies=dependencies or ["can_interface"],
            friendly_name=friendly_name or "Multi-Network CAN Manager",
        )
        self.manager = get_multi_network_manager()
        self.settings = get_multi_network_settings()
        self._started = False

    async def startup(self) -> None:
        """Initialize the multi-network CAN feature."""
        if not self.settings.enabled:
            logger.info("Multi-network CAN feature disabled by configuration")
            return

        try:
            logger.info("Starting multi-network CAN feature...")
            await self.manager.startup()
            self._started = True
            logger.info("Multi-network CAN feature started successfully")

        except Exception as e:
            logger.error(f"Failed to start multi-network CAN feature: {e}")
            self._started = False
            raise

    async def shutdown(self) -> None:
        """Shutdown the multi-network CAN feature."""
        if not self._started:
            return

        try:
            logger.info("Shutting down multi-network CAN feature...")
            await self.manager.shutdown()
            self._started = False
            logger.info("Multi-network CAN feature shutdown complete")

        except Exception as e:
            logger.error(f"Error during multi-network CAN feature shutdown: {e}")

    @property
    def health(self) -> str:
        """Get the health status of the multi-network feature."""
        if not self.settings.enabled:
            return "healthy"  # Disabled features are considered healthy

        if not self._started:
            return "degraded"  # Not started but enabled

        try:
            # Check if any networks are operational
            status = self.manager.get_all_networks_status()
            operational_networks = status["summary"]["operational_networks"]

            if operational_networks == 0:
                return "failed"  # No operational networks
            elif operational_networks < len(status["networks"]):
                return "degraded"  # Some networks not operational
            else:
                return "healthy"  # All networks operational

        except Exception as e:
            logger.error(f"Health check failed for multi-network CAN feature: {e}")
            return "failed"

    def is_healthy(self) -> bool:
        """Check if the multi-network feature is healthy."""
        return self.health == "healthy"

    def get_status(self) -> dict[str, Any]:
        """Get comprehensive status of the multi-network feature."""
        base_status = {
            "feature_name": "multi_network_can",
            "enabled": self.settings.enabled,
            "started": self._started,
            "healthy": self.is_healthy(),
        }

        if not self.settings.enabled:
            base_status["reason"] = "Feature disabled by configuration"
            return base_status

        if not self._started:
            base_status["reason"] = "Feature not started"
            return base_status

        try:
            # Get detailed status from manager
            manager_status = self.manager.get_all_networks_status()
            base_status.update(
                {
                    "networks": manager_status["networks"],
                    "summary": manager_status["summary"],
                    "metrics": manager_status["metrics"],
                    "configuration": {
                        "health_monitoring": self.settings.enable_health_monitoring,
                        "fault_isolation": self.settings.enable_fault_isolation,
                        "cross_network_routing": self.settings.enable_cross_network_routing,
                        "max_networks": self.settings.max_networks,
                        "health_check_interval": self.settings.health_check_interval,
                    },
                }
            )

        except Exception as e:
            logger.error(f"Failed to get multi-network status: {e}")
            base_status["error"] = str(e)
            base_status["healthy"] = False

        return base_status

    # Public API methods for network management

    async def register_network(
        self,
        network_id: str,
        interface: str,
        protocol: str,
        priority: str = "normal",
        isolation_enabled: bool = True,
        description: str = "",
    ) -> bool:
        """Register a new CAN network."""
        if not self._started:
            logger.warning("Cannot register network: multi-network feature not started")
            return False

        return await self.manager.register_network(
            network_id=network_id,
            interface=interface,
            protocol=protocol,
            priority=priority,
            isolation_enabled=isolation_enabled,
            description=description,
        )

    async def unregister_network(self, network_id: str) -> bool:
        """Unregister a CAN network."""
        if not self._started:
            logger.warning("Cannot unregister network: multi-network feature not started")
            return False

        return await self.manager.unregister_network(network_id)

    def get_network_status(self, network_id: str) -> dict[str, Any] | None:
        """Get status of a specific network."""
        if not self._started:
            return None

        return self.manager.get_network_status(network_id)

    def get_network_by_interface(self, interface: str) -> str | None:
        """Get network ID by interface name."""
        if not self._started:
            return None

        return self.manager.get_network_by_interface(interface)

    async def isolate_network(self, network_id: str, reason: str = "") -> bool:
        """Manually isolate a network."""
        if not self._started:
            logger.warning("Cannot isolate network: multi-network feature not started")
            return False

        return await self.manager.isolate_network(network_id, reason)

    async def recover_network(self, network_id: str) -> bool:
        """Manually attempt network recovery."""
        if not self._started:
            logger.warning("Cannot recover network: multi-network feature not started")
            return False

        return await self.manager.recover_network(network_id)

    def get_networks_by_protocol(self, protocol: str) -> list[dict[str, Any]]:
        """Get all networks using a specific protocol."""
        if not self._started:
            return []

        try:
            from backend.integrations.can.multi_network_manager import ProtocolType

            protocol_enum = ProtocolType(protocol.lower())

            networks = self.manager.registry.get_networks_by_protocol(protocol_enum)
            return [
                {
                    "network_id": net.network_id,
                    "interface": net.interface,
                    "protocol": net.protocol.value,
                    "priority": net.priority.value,
                    "status": net.health.status.value,
                    "description": net.description,
                }
                for net in networks
            ]

        except ValueError:
            logger.warning(f"Invalid protocol: {protocol}")
            return []
        except Exception as e:
            logger.error(f"Error getting networks by protocol: {e}")
            return []


# Global feature instance
_multi_network_feature: MultiNetworkCANFeature | None = None


def get_multi_network_feature() -> MultiNetworkCANFeature:
    """Get the global multi-network CAN feature instance."""
    global _multi_network_feature
    if _multi_network_feature is None:
        _multi_network_feature = MultiNetworkCANFeature()
    return _multi_network_feature
