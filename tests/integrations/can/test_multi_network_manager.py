"""
Comprehensive tests for the multi-network CAN manager.

Tests cover:
- Network registration and management
- Health monitoring and fault detection
- Network isolation and recovery
- Configuration integration
- Feature integration
"""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.integrations.can.multi_network_feature import MultiNetworkCANFeature
from backend.integrations.can.multi_network_manager import (
    MultiNetworkManager,
    NetworkHealth,
    NetworkNode,
    NetworkPriority,
    NetworkRegistry,
    NetworkStatus,
    ProtocolType,
)


class TestNetworkRegistry:
    """Test the NetworkRegistry class."""

    @pytest.fixture
    def registry(self):
        """Create a NetworkRegistry instance."""
        return NetworkRegistry()

    @pytest.mark.asyncio
    async def test_register_network(self, registry):
        """Test network registration."""
        network = await registry.register_network(
            network_id="test_network",
            interface="can0",
            protocol=ProtocolType.RVC,
            priority=NetworkPriority.HIGH,
            description="Test network",
        )

        assert network.network_id == "test_network"
        assert network.interface == "can0"
        assert network.protocol == ProtocolType.RVC
        assert network.priority == NetworkPriority.HIGH
        assert network.description == "Test network"

        # Check registry state
        assert "test_network" in registry.networks
        assert registry.interface_mapping["can0"] == "test_network"

    @pytest.mark.asyncio
    async def test_register_duplicate_network(self, registry):
        """Test registering duplicate network fails."""
        await registry.register_network(
            network_id="test_network", interface="can0", protocol=ProtocolType.RVC
        )

        with pytest.raises(ValueError, match="already registered"):
            await registry.register_network(
                network_id="test_network", interface="can1", protocol=ProtocolType.J1939
            )

    @pytest.mark.asyncio
    async def test_unregister_network(self, registry):
        """Test network unregistration."""
        # Register a network
        network = await registry.register_network(
            network_id="test_network", interface="can0", protocol=ProtocolType.RVC
        )

        # Mock bus for cleanup
        network.bus = MagicMock()

        # Unregister
        result = await registry.unregister_network("test_network")

        assert result is True
        assert "test_network" not in registry.networks
        assert "can0" not in registry.interface_mapping
        network.bus.shutdown.assert_called_once()

    @pytest.mark.asyncio
    async def test_unregister_nonexistent_network(self, registry):
        """Test unregistering non-existent network."""
        result = await registry.unregister_network("nonexistent")
        assert result is False

    def test_get_network_by_interface(self, registry):
        """Test getting network by interface."""
        # No networks registered
        assert registry.get_network_by_interface("can0") is None

        # Add to internal state for testing
        network = NetworkNode(
            network_id="test_network",
            interface="can0",
            protocol=ProtocolType.RVC,
            priority=NetworkPriority.NORMAL,
        )
        registry.networks["test_network"] = network
        registry.interface_mapping["can0"] = "test_network"

        result = registry.get_network_by_interface("can0")
        assert result == network

    def test_get_networks_by_protocol(self, registry):
        """Test getting networks by protocol."""
        # Add networks to internal state
        rvc_network = NetworkNode(
            network_id="rvc_network",
            interface="can0",
            protocol=ProtocolType.RVC,
            priority=NetworkPriority.NORMAL,
        )
        j1939_network = NetworkNode(
            network_id="j1939_network",
            interface="can1",
            protocol=ProtocolType.J1939,
            priority=NetworkPriority.HIGH,
        )

        registry.networks["rvc_network"] = rvc_network
        registry.networks["j1939_network"] = j1939_network

        rvc_networks = registry.get_networks_by_protocol(ProtocolType.RVC)
        assert len(rvc_networks) == 1
        assert rvc_networks[0] == rvc_network

        j1939_networks = registry.get_networks_by_protocol(ProtocolType.J1939)
        assert len(j1939_networks) == 1
        assert j1939_networks[0] == j1939_network

    def test_status_summary(self, registry):
        """Test status summary generation."""
        # Empty registry
        summary = registry.get_status_summary()
        assert summary["total_networks"] == 0
        assert summary["healthy_networks"] == 0
        assert summary["operational_networks"] == 0

        # Add networks
        healthy_network = NetworkNode(
            network_id="healthy",
            interface="can0",
            protocol=ProtocolType.RVC,
            priority=NetworkPriority.NORMAL,
        )
        healthy_network.health.status = NetworkStatus.HEALTHY

        faulted_network = NetworkNode(
            network_id="faulted",
            interface="can1",
            protocol=ProtocolType.J1939,
            priority=NetworkPriority.HIGH,
        )
        faulted_network.health.status = NetworkStatus.FAULTED

        registry.networks["healthy"] = healthy_network
        registry.networks["faulted"] = faulted_network

        summary = registry.get_status_summary()
        assert summary["total_networks"] == 2
        assert summary["healthy_networks"] == 1
        assert summary["operational_networks"] == 1  # Only healthy is operational
        assert summary["status_distribution"]["healthy"] == 1
        assert summary["status_distribution"]["faulted"] == 1


class TestNetworkNode:
    """Test the NetworkNode class."""

    def test_initialization(self):
        """Test network node initialization."""
        network = NetworkNode(
            network_id="test",
            interface="can0",
            protocol=ProtocolType.RVC,
            priority=NetworkPriority.HIGH,
        )

        assert network.network_id == "test"
        assert network.interface == "can0"
        assert network.protocol == ProtocolType.RVC
        assert network.priority == NetworkPriority.HIGH
        assert network.isolation_enabled is True
        assert network.description == "RVC network on can0"
        assert isinstance(network.health, NetworkHealth)

    def test_health_properties(self):
        """Test health status properties."""
        network = NetworkNode(
            network_id="test",
            interface="can0",
            protocol=ProtocolType.RVC,
            priority=NetworkPriority.NORMAL,
        )

        # Initial state
        assert not network.is_healthy
        assert not network.is_operational

        # Set healthy
        network.health.status = NetworkStatus.HEALTHY
        assert network.is_healthy
        assert network.is_operational

        # Set degraded
        network.health.status = NetworkStatus.DEGRADED
        assert not network.is_healthy
        assert network.is_operational  # Degraded is still operational

        # Set faulted
        network.health.status = NetworkStatus.FAULTED
        assert not network.is_healthy
        assert not network.is_operational

    def test_uptime_calculation(self):
        """Test uptime calculation."""
        start_time = time.time()
        network = NetworkNode(
            network_id="test",
            interface="can0",
            protocol=ProtocolType.RVC,
            priority=NetworkPriority.NORMAL,
        )
        network.start_time = start_time

        # Allow some time to pass
        time.sleep(0.1)

        uptime = network.uptime_seconds
        assert uptime >= 0.1
        assert uptime < 1.0  # Should be small


class TestMultiNetworkManager:
    """Test the MultiNetworkManager class."""

    @pytest.fixture
    def manager(self):
        """Create a MultiNetworkManager instance."""
        with patch(
            "backend.integrations.can.multi_network_manager.get_multi_network_settings"
        ) as mock_settings:
            # Mock settings
            mock_settings.return_value.enabled = True
            mock_settings.return_value.enable_health_monitoring = True
            mock_settings.return_value.enable_fault_isolation = True
            mock_settings.return_value.enable_cross_network_routing = False
            mock_settings.return_value.health_check_interval = 1
            mock_settings.return_value.default_networks = {}

            with patch(
                "backend.integrations.can.multi_network_manager.get_can_settings"
            ) as mock_can_settings:
                mock_can_settings.return_value.bustype = "virtual"
                mock_can_settings.return_value.bitrate = 500000

                return MultiNetworkManager()

    @pytest.mark.asyncio
    async def test_startup_disabled(self):
        """Test startup when disabled."""
        with patch(
            "backend.integrations.can.multi_network_manager.get_multi_network_settings"
        ) as mock_settings:
            mock_settings.return_value.enabled = False

            manager = MultiNetworkManager()
            await manager.startup()

            # Should not start any background tasks
            assert manager._health_monitor_task is None
            assert manager._router_task is None

    @pytest.mark.asyncio
    async def test_startup_enabled(self, manager):
        """Test startup when enabled."""
        with (
            patch.object(
                manager, "_register_default_networks", new_callable=AsyncMock
            ) as mock_register,
            patch.object(
                manager, "_start_health_monitoring", new_callable=AsyncMock
            ) as mock_health,
        ):
            await manager.startup()

            mock_register.assert_called_once()
            mock_health.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_network(self, manager):
        """Test network registration through manager."""
        with patch.object(manager, "_initialize_network_bus", new_callable=AsyncMock) as mock_init:
            mock_init.return_value = True

            result = await manager.register_network(
                network_id="test",
                interface="can0",
                protocol="rvc",
                priority="high",
                description="Test network",
            )

            assert result is True
            assert "test" in manager.registry.networks
            mock_init.assert_called_once_with("test")

    @pytest.mark.asyncio
    async def test_register_network_invalid_protocol(self, manager):
        """Test registering network with invalid protocol."""
        result = await manager.register_network(
            network_id="test", interface="can0", protocol="invalid_protocol"
        )

        assert result is False
        assert "test" not in manager.registry.networks

    @pytest.mark.asyncio
    async def test_unregister_network(self, manager):
        """Test network unregistration through manager."""
        # First register a network
        await manager.registry.register_network(
            network_id="test",
            interface="can0",
            protocol=ProtocolType.RVC,
            priority=NetworkPriority.NORMAL,
        )

        result = await manager.unregister_network("test")
        assert result is True
        assert "test" not in manager.registry.networks

    def test_get_network_status(self, manager):
        """Test getting network status."""
        # Non-existent network
        status = manager.get_network_status("nonexistent")
        assert status is None

        # Add a network directly to registry for testing
        network = NetworkNode(
            network_id="test",
            interface="can0",
            protocol=ProtocolType.RVC,
            priority=NetworkPriority.HIGH,
        )
        network.health.status = NetworkStatus.HEALTHY
        network.health.message_count = 100

        manager.registry.networks["test"] = network

        status = manager.get_network_status("test")
        assert status is not None
        assert status["network_id"] == "test"
        assert status["interface"] == "can0"
        assert status["protocol"] == "rvc"
        assert status["priority"] == "high"
        assert status["status"] == "healthy"
        assert status["message_count"] == 100

    def test_get_all_networks_status(self, manager):
        """Test getting all networks status."""
        status = manager.get_all_networks_status()

        assert "networks" in status
        assert "summary" in status
        assert "metrics" in status
        assert "settings" in status

        # Check settings
        settings = status["settings"]
        assert "enabled" in settings
        assert "health_monitoring" in settings
        assert "fault_isolation" in settings

    @pytest.mark.asyncio
    async def test_isolate_network(self, manager):
        """Test manually isolating a network."""
        # Add a network with mock bus
        network = NetworkNode(
            network_id="test",
            interface="can0",
            protocol=ProtocolType.RVC,
            priority=NetworkPriority.NORMAL,
        )
        network.bus = MagicMock()
        network.health.status = NetworkStatus.HEALTHY

        manager.registry.networks["test"] = network

        result = await manager.isolate_network("test", "Test isolation")

        assert result is True
        assert network.health.status == NetworkStatus.ISOLATED
        assert "Test isolation" in network.health.last_error
        network.bus.shutdown.assert_called_once()
        assert network.bus is None

    @pytest.mark.asyncio
    async def test_recover_network(self, manager):
        """Test manually recovering a network."""
        # Add a faulted network
        network = NetworkNode(
            network_id="test",
            interface="can0",
            protocol=ProtocolType.RVC,
            priority=NetworkPriority.NORMAL,
        )
        network.health.status = NetworkStatus.FAULTED

        manager.registry.networks["test"] = network

        with patch.object(
            manager, "_attempt_network_recovery", new_callable=AsyncMock
        ) as mock_recover:
            mock_recover.return_value = True

            result = await manager.recover_network("test")

            assert result is True
            mock_recover.assert_called_once_with(network)

    @pytest.mark.asyncio
    async def test_health_monitoring(self, manager):
        """Test health monitoring functionality."""
        # Add a network
        network = NetworkNode(
            network_id="test",
            interface="can0",
            protocol=ProtocolType.RVC,
            priority=NetworkPriority.NORMAL,
        )
        network.health.status = NetworkStatus.HEALTHY
        network.health.last_message_time = time.time() - 50  # 50 seconds ago

        manager.registry.networks["test"] = network

        # Perform health check
        await manager._perform_health_checks()

        # Should be degraded due to message timeout
        assert network.health.status == NetworkStatus.DEGRADED
        assert manager.metrics["health_checks"] == 1


class TestMultiNetworkCANFeature:
    """Test the MultiNetworkCANFeature class."""

    @pytest.fixture
    def feature(self):
        """Create a MultiNetworkCANFeature instance."""
        with patch(
            "backend.integrations.can.multi_network_feature.get_multi_network_settings"
        ) as mock_settings:
            mock_settings.return_value.enabled = True

            with patch(
                "backend.integrations.can.multi_network_feature.get_multi_network_manager"
            ) as mock_manager:
                mock_manager.return_value = MagicMock()
                return MultiNetworkCANFeature()

    @pytest.mark.asyncio
    async def test_startup_disabled(self):
        """Test feature startup when disabled."""
        with patch(
            "backend.integrations.can.multi_network_feature.get_multi_network_settings"
        ) as mock_settings:
            mock_settings.return_value.enabled = False

            feature = MultiNetworkCANFeature()
            await feature.startup()

            assert not feature._started

    @pytest.mark.asyncio
    async def test_startup_enabled(self, feature):
        """Test feature startup when enabled."""
        feature.manager.startup = AsyncMock()

        await feature.startup()

        assert feature._started
        feature.manager.startup.assert_called_once()

    @pytest.mark.asyncio
    async def test_startup_failure(self, feature):
        """Test feature startup failure handling."""
        feature.manager.startup = AsyncMock(side_effect=Exception("Startup failed"))

        with pytest.raises(Exception, match="Startup failed"):
            await feature.startup()

        assert not feature._started

    @pytest.mark.asyncio
    async def test_shutdown(self, feature):
        """Test feature shutdown."""
        feature._started = True
        feature.manager.shutdown = AsyncMock()

        await feature.shutdown()

        assert not feature._started
        feature.manager.shutdown.assert_called_once()

    def test_is_healthy_disabled(self):
        """Test health check when disabled."""
        with patch(
            "backend.integrations.can.multi_network_feature.get_multi_network_settings"
        ) as mock_settings:
            mock_settings.return_value.enabled = False

            feature = MultiNetworkCANFeature()
            assert feature.is_healthy() is True

    def test_is_healthy_not_started(self, feature):
        """Test health check when not started."""
        feature._started = False
        assert feature.is_healthy() is True

    def test_is_healthy_operational(self, feature):
        """Test health check when operational."""
        feature._started = True
        feature.manager.get_all_networks_status.return_value = {
            "summary": {"operational_networks": 2}
        }

        assert feature.is_healthy() is True

    def test_is_healthy_no_operational_networks(self, feature):
        """Test health check with no operational networks."""
        feature._started = True
        feature.manager.get_all_networks_status.return_value = {
            "summary": {"operational_networks": 0}
        }

        assert feature.is_healthy() is False

    def test_get_status_disabled(self):
        """Test getting status when disabled."""
        with patch(
            "backend.integrations.can.multi_network_feature.get_multi_network_settings"
        ) as mock_settings:
            mock_settings.return_value.enabled = False

            feature = MultiNetworkCANFeature()
            status = feature.get_status()

            assert status["enabled"] is False
            assert status["reason"] == "Feature disabled by configuration"

    def test_get_status_not_started(self, feature):
        """Test getting status when not started."""
        feature._started = False
        status = feature.get_status()

        assert status["started"] is False
        assert status["reason"] == "Feature not started"

    def test_get_status_operational(self, feature):
        """Test getting status when operational."""
        feature._started = True
        feature.manager.get_all_networks_status.return_value = {
            "networks": {},
            "summary": {"operational_networks": 1},
            "metrics": {"messages_routed": 100},
        }

        status = feature.get_status()

        assert status["started"] is True
        assert status["healthy"] is True
        assert "networks" in status
        assert "summary" in status
        assert "metrics" in status
        assert "configuration" in status

    @pytest.mark.asyncio
    async def test_register_network_not_started(self, feature):
        """Test registering network when feature not started."""
        feature._started = False

        result = await feature.register_network("test", "can0", "rvc")
        assert result is False

    @pytest.mark.asyncio
    async def test_register_network_started(self, feature):
        """Test registering network when feature started."""
        feature._started = True
        feature.manager.register_network = AsyncMock(return_value=True)

        result = await feature.register_network("test", "can0", "rvc")

        assert result is True
        feature.manager.register_network.assert_called_once_with(
            network_id="test",
            interface="can0",
            protocol="rvc",
            priority="normal",
            isolation_enabled=True,
            description="",
        )


@pytest.mark.integration
class TestMultiNetworkIntegration:
    """Integration tests for multi-network functionality."""

    @pytest.mark.asyncio
    async def test_full_lifecycle(self):
        """Test complete multi-network lifecycle."""
        with patch(
            "backend.integrations.can.multi_network_manager.get_multi_network_settings"
        ) as mock_settings:
            # Configure settings
            mock_settings.return_value.enabled = True
            mock_settings.return_value.enable_health_monitoring = False  # Disable for simpler test
            mock_settings.return_value.enable_cross_network_routing = False
            mock_settings.return_value.default_networks = {}

            with patch(
                "backend.integrations.can.multi_network_manager.get_can_settings"
            ) as mock_can_settings:
                mock_can_settings.return_value.bustype = "virtual"
                mock_can_settings.return_value.bitrate = 500000

                # Create manager
                manager = MultiNetworkManager()

                # Startup
                await manager.startup()

                # Register a network (will fail bus init but that's OK for test)
                with patch.object(
                    manager, "_initialize_network_bus", new_callable=AsyncMock
                ) as mock_init:
                    mock_init.return_value = True

                    result = await manager.register_network(
                        network_id="house", interface="vcan0", protocol="rvc", priority="high"
                    )

                    assert result is True

                # Check status
                status = manager.get_all_networks_status()
                assert "house" in status["networks"]
                assert status["summary"]["total_networks"] == 1

                # Unregister network
                result = await manager.unregister_network("house")
                assert result is True

                # Shutdown
                await manager.shutdown()

                assert len(manager.registry.networks) == 0
