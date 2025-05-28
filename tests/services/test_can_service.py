"""
Test suite for CANService.

Tests the CAN service business logic, including:
- CAN bus status and queue monitoring
- Raw CAN message sending
- CAN bus management operations
- Interface information retrieval
"""

import asyncio
from unittest.mock import AsyncMock, Mock, PropertyMock, patch

import pytest

from backend.services.can_service import CANService

# ================================
# Test Fixtures
# ================================


@pytest.fixture
def mock_app_state():
    """Mock AppState for testing."""
    mock = Mock()
    mock.some_attribute = "test_value"
    return mock


@pytest.fixture
def can_service(mock_app_state):
    """Create CANService instance for testing."""
    return CANService(app_state=mock_app_state)


@pytest.fixture
def can_service_no_state():
    """Create CANService instance without app_state for testing."""
    return CANService()


@pytest.fixture
def mock_can_message():
    """Create a mock CAN message for testing."""
    mock_msg = Mock()
    mock_msg.arbitration_id = 0x18EEFF00
    mock_msg.data = b"\x01\x02\x03\x04\x05\x06\x07\x08"
    mock_msg.is_extended_id = True
    mock_msg.timestamp = 1234567890.123
    return mock_msg


@pytest.fixture
def mock_can_bus():
    """Create a mock CAN bus for testing."""
    mock_bus = Mock()
    mock_bus.channel = "vcan0"
    mock_bus.bus_type = "socketcan"
    mock_bus.get_stats = Mock(
        return_value={"messages_sent": 100, "messages_received": 200, "errors": 5}
    )
    return mock_bus


# ================================
# Core Functionality Tests
# ================================


class TestCANServiceInitialization:
    """Test CANService initialization and setup."""

    def test_init_with_app_state(self, mock_app_state):
        """Test service initialization with app_state."""
        service = CANService(app_state=mock_app_state)
        assert service.app_state is mock_app_state

    def test_init_without_app_state(self):
        """Test service initialization without app_state."""
        service = CANService()
        assert service.app_state is None


# ================================
# Queue Status Tests
# ================================


class TestQueueStatus:
    """Test CAN queue status functionality."""

    @patch("backend.services.can_service.can_tx_queue")
    async def test_get_queue_status_basic(self, mock_queue, can_service):
        """Test basic queue status retrieval."""
        mock_queue.qsize.return_value = 5
        mock_queue.maxsize = 100

        result = await can_service.get_queue_status()

        assert result == {"length": 5, "maxsize": 100}
        mock_queue.qsize.assert_called_once()

    @patch("backend.services.can_service.can_tx_queue")
    async def test_get_queue_status_unbounded(self, mock_queue, can_service):
        """Test queue status with unbounded queue."""
        mock_queue.qsize.return_value = 10
        mock_queue.maxsize = None

        result = await can_service.get_queue_status()

        assert result == {"length": 10, "maxsize": "unbounded"}

    @patch("backend.services.can_service.can_tx_queue")
    async def test_get_queue_status_empty(self, mock_queue, can_service):
        """Test queue status when queue is empty."""
        mock_queue.qsize.return_value = 0
        mock_queue.maxsize = 50

        result = await can_service.get_queue_status()

        assert result == {"length": 0, "maxsize": 50}


# ================================
# Interface Management Tests
# ================================


class TestInterfaceManagement:
    """Test CAN interface management functionality."""

    @patch("backend.services.can_service.buses")
    async def test_get_interfaces_basic(self, mock_buses, can_service):
        """Test basic interface retrieval."""
        mock_buses.keys.return_value = ["vcan0", "vcan1", "can0"]

        result = await can_service.get_interfaces()

        assert result == ["vcan0", "vcan1", "can0"]

    @patch("backend.services.can_service.buses")
    async def test_get_interfaces_empty(self, mock_buses, can_service):
        """Test interface retrieval when no interfaces are active."""
        mock_buses.keys.return_value = []

        result = await can_service.get_interfaces()

        assert result == []

    @patch("backend.services.can_service.buses")
    async def test_get_interface_details_single(self, mock_buses, can_service, mock_can_bus):
        """Test detailed interface information for single interface."""
        mock_buses.items.return_value = [("vcan0", mock_can_bus)]

        result = await can_service.get_interface_details()

        expected = {
            "vcan0": {
                "name": "vcan0",
                "channel": "vcan0",
                "bustype": "socketcan",
                "state": "active",
                "stats": {"messages_sent": 100, "messages_received": 200, "errors": 5},
            }
        }
        assert result == expected

    @patch("backend.services.can_service.buses")
    async def test_get_interface_details_multiple(self, mock_buses, can_service):
        """Test detailed interface information for multiple interfaces."""
        mock_bus1 = Mock()
        mock_bus1.channel = "vcan0"
        mock_bus1.bus_type = "socketcan"

        mock_bus2 = Mock()
        mock_bus2.channel = "can0"
        mock_bus2.bus_type = "socketcan"

        mock_buses.items.return_value = [("vcan0", mock_bus1), ("can0", mock_bus2)]

        result = await can_service.get_interface_details()

        assert len(result) == 2
        assert "vcan0" in result
        assert "can0" in result
        assert result["vcan0"]["name"] == "vcan0"
        assert result["can0"]["name"] == "can0"

    @patch("backend.services.can_service.buses")
    async def test_get_interface_details_no_stats(self, mock_buses, can_service):
        """Test interface details when bus doesn't support stats."""
        mock_bus = Mock()
        mock_bus.channel = "vcan0"
        mock_bus.bus_type = "socketcan"
        # Explicitly remove get_stats to ensure hasattr returns False
        del mock_bus.get_stats

        mock_buses.items.return_value = [("vcan0", mock_bus)]

        result = await can_service.get_interface_details()

        expected = {
            "vcan0": {
                "name": "vcan0",
                "channel": "vcan0",
                "bustype": "socketcan",
                "state": "active",
            }
        }
        assert result == expected

    @patch("backend.services.can_service.buses")
    async def test_get_interface_details_with_error(self, mock_buses, can_service):
        """Test interface details when an error occurs."""
        mock_bus = Mock()
        mock_bus.channel = "vcan0"
        mock_bus.bus_type = "socketcan"
        # Make hasattr return True but get_stats raises an error
        mock_bus.get_stats = Mock(side_effect=RuntimeError("Stats error"))

        mock_buses.items.return_value = [("vcan0", mock_bus)]

        result = await can_service.get_interface_details()

        expected = {
            "vcan0": {
                "name": "vcan0",
                "channel": "vcan0",
                "bustype": "socketcan",
                "state": "active",
            }
        }
        assert result == expected

    @patch("backend.services.can_service.buses")
    async def test_get_interface_details_bus_failure(self, mock_buses, can_service):
        """Test interface details when bus access fails."""
        mock_bus = Mock()
        # Simulate getattr failing for channel
        type(mock_bus).channel = PropertyMock(side_effect=RuntimeError("Bus error"))

        mock_buses.items.return_value = [("vcan0", mock_bus)]

        result = await can_service.get_interface_details()

        assert "vcan0" in result
        assert result["vcan0"]["state"] == "error"
        assert "error" in result["vcan0"]

    @patch("backend.services.can_service.buses")
    async def test_get_interface_details_inactive_bus(self, mock_buses, can_service):
        """Test interface details with inactive/None bus."""
        mock_buses.items.return_value = [("vcan0", None)]

        result = await can_service.get_interface_details()

        expected = {
            "vcan0": {
                "name": "vcan0",
                "channel": "unknown",
                "bustype": "unknown",
                "state": "inactive",
            }
        }
        assert result == expected


# ================================
# Message Sending Tests
# ================================


class TestMessageSending:
    """Test raw CAN message sending functionality."""

    @patch("backend.services.can_service.buses")
    @patch("backend.services.can_service.can_tx_queue")
    async def test_send_raw_message_success(
        self, mock_queue, mock_buses, can_service, mock_can_bus
    ):
        """Test successful raw message sending."""
        mock_buses.__contains__ = Mock(return_value=True)
        mock_buses.__getitem__ = Mock(return_value=mock_can_bus)
        mock_buses.keys.return_value = ["vcan0"]
        # Create an async mock for the queue put operation
        mock_queue.put = AsyncMock()
        mock_queue.qsize.return_value = 1

        arbitration_id = 0x18EEFF00
        data = b"\x01\x02\x03\x04"
        interface = "vcan0"

        result = await can_service.send_raw_message(arbitration_id, data, interface)

        # Verify async queue.put was called
        mock_queue.put.assert_called_once()
        call_args = mock_queue.put.call_args[0]
        message_tuple = call_args[0]

        assert len(message_tuple) == 2
        assert message_tuple[1] == interface  # Interface name

        # Check the CAN message
        can_message = message_tuple[0]
        assert can_message.arbitration_id == arbitration_id
        assert can_message.data == data
        assert can_message.is_extended_id is True

        # Check return value - service returns "queued" not "success"
        assert result["status"] == "queued"
        assert result["arbitration_id"] == arbitration_id
        assert result["data"] == data.hex().upper()
        assert result["interface"] == interface
        assert result["queue_size"] == 1

    @patch("backend.services.can_service.buses")
    async def test_send_raw_message_interface_not_found(self, mock_buses, can_service):
        """Test message sending when interface doesn't exist."""
        mock_buses.__contains__ = Mock(return_value=False)
        mock_buses.keys.return_value = []

        arbitration_id = 0x18EEFF00
        data = b"\x01\x02\x03\x04"
        interface = "nonexistent"

        with pytest.raises(ValueError, match="Interface 'nonexistent' not found"):
            await can_service.send_raw_message(arbitration_id, data, interface)

    @patch("backend.services.can_service.buses")
    @patch("backend.services.can_service.can_tx_queue")
    async def test_send_raw_message_queue_full(
        self, mock_queue, mock_buses, can_service, mock_can_bus
    ):
        """Test message sending when queue is full."""
        mock_buses.__contains__ = Mock(return_value=True)
        mock_buses.__getitem__ = Mock(return_value=mock_can_bus)
        mock_buses.keys.return_value = ["vcan0"]
        mock_queue.put = AsyncMock(side_effect=asyncio.QueueFull("Queue is full"))
        mock_queue.qsize.return_value = 10

        arbitration_id = 0x18EEFF00
        data = b"\x01\x02\x03\x04"
        interface = "vcan0"

        # Service catches the exception and returns error status
        result = await can_service.send_raw_message(arbitration_id, data, interface)
        assert result["status"] == "error"
        assert "Queue is full" in result["error"]

    @patch("backend.services.can_service.buses")
    @patch("backend.services.can_service.can_tx_queue")
    async def test_send_raw_message_long_data(
        self, mock_queue, mock_buses, can_service, mock_can_bus
    ):
        """Test message sending with data that is too long (should fail validation)."""
        mock_buses.__contains__ = Mock(return_value=True)
        mock_buses.__getitem__ = Mock(return_value=mock_can_bus)
        mock_buses.keys.return_value = ["vcan0"]

        arbitration_id = 0x18EEFF00
        data = b"\x01\x02\x03\x04\x05\x06\x07\x08\x09"  # 9 bytes - too long
        interface = "vcan0"

        # Should raise ValueError due to data length validation
        with pytest.raises(ValueError, match="CAN data too long: 9 bytes"):
            await can_service.send_raw_message(arbitration_id, data, interface)

    @patch("backend.services.can_service.buses")
    @patch("backend.services.can_service.can_tx_queue")
    async def test_send_raw_message_max_data(
        self, mock_queue, mock_buses, can_service, mock_can_bus
    ):
        """Test message sending with maximum valid data length (8 bytes)."""
        mock_buses.__contains__ = Mock(return_value=True)
        mock_buses.__getitem__ = Mock(return_value=mock_can_bus)
        mock_buses.keys.return_value = ["vcan0"]
        mock_queue.put = AsyncMock()
        mock_queue.qsize.return_value = 1

        arbitration_id = 0x18EEFF00
        data = b"\x01\x02\x03\x04\x05\x06\x07\x08"  # 8 bytes - max for CAN
        interface = "vcan0"

        result = await can_service.send_raw_message(arbitration_id, data, interface)

        assert result["status"] == "queued"
        assert result["data"] == "0102030405060708"
        mock_queue.put.assert_called_once()

    @patch("backend.services.can_service.buses")
    async def test_send_raw_message_invalid_data_length(
        self, mock_buses, can_service, mock_can_bus
    ):
        """Test message sending with invalid data length."""
        mock_buses.__contains__ = Mock(return_value=True)

        arbitration_id = 0x18EEFF00
        data = b"\x01\x02\x03\x04\x05\x06\x07\x08\x09"  # 9 bytes - too long
        interface = "vcan0"

        with pytest.raises(ValueError, match="CAN data too long: 9 bytes"):
            await can_service.send_raw_message(arbitration_id, data, interface)

    @patch("backend.services.can_service.buses")
    async def test_send_raw_message_invalid_arbitration_id(
        self, mock_buses, can_service, mock_can_bus
    ):
        """Test message sending with invalid arbitration ID."""
        mock_buses.__getitem__.return_value = mock_can_bus

        # Test with negative ID
        with pytest.raises(ValueError, match="Invalid arbitration ID"):
            await can_service.send_raw_message(-1, b"\x01", "vcan0")

        # Test with ID too large for extended frame
        with pytest.raises(ValueError, match="Invalid arbitration ID"):
            await can_service.send_raw_message(0x20000000, b"\x01", "vcan0")

    @patch("backend.services.can_service.buses")
    @patch("backend.services.can_service.can_tx_queue")
    async def test_send_raw_message_empty_data(
        self, mock_queue, mock_buses, can_service, mock_can_bus
    ):
        """Test message sending with empty data."""
        mock_buses.__contains__ = Mock(return_value=True)
        mock_buses.__getitem__ = Mock(return_value=mock_can_bus)
        mock_buses.keys.return_value = ["vcan0"]
        mock_queue.put = AsyncMock()
        mock_queue.qsize.return_value = 1

        arbitration_id = 0x18EEFF00
        data = b""
        interface = "vcan0"

        result = await can_service.send_raw_message(arbitration_id, data, interface)

        assert result["status"] == "queued"
        assert result["data"] == ""
        mock_queue.put.assert_called_once()


# ================================
# Error Handling Tests
# ================================


class TestErrorHandling:
    """Test error handling in various scenarios."""

    @patch("backend.services.can_service.buses")
    async def test_interface_details_partial_failure(self, mock_buses, can_service):
        """Test that partial failures don't break the entire operation."""
        mock_good_bus = Mock()
        mock_good_bus.channel = "vcan0"
        mock_good_bus.bus_type = "socketcan"

        mock_bad_bus = Mock()
        type(mock_bad_bus).channel = PropertyMock(side_effect=RuntimeError("Bad bus"))

        mock_buses.items.return_value = [("vcan0", mock_good_bus), ("bad_bus", mock_bad_bus)]

        result = await can_service.get_interface_details()

        assert len(result) == 2
        assert result["vcan0"]["state"] == "active"
        assert result["bad_bus"]["state"] == "error"

    @patch("backend.services.can_service.can_tx_queue")
    async def test_queue_status_access_error(self, mock_queue, can_service):
        """Test queue status when queue access fails."""
        mock_queue.qsize.side_effect = RuntimeError("Queue access error")

        with pytest.raises(RuntimeError):
            await can_service.get_queue_status()


# ================================
# Integration Tests
# ================================


class TestServiceIntegration:
    """Test service integration with dependencies."""

    def test_service_with_app_state_integration(self, mock_app_state):
        """Test that service properly integrates with app_state."""
        service = CANService(app_state=mock_app_state)

        assert service.app_state is mock_app_state
        # Service should be able to access app_state attributes
        assert hasattr(service.app_state, "some_attribute")

    @patch("backend.services.can_service.buses")
    @patch("backend.services.can_service.can_tx_queue")
    async def test_end_to_end_message_flow(self, mock_queue, mock_buses, can_service, mock_can_bus):
        """Test complete message sending flow."""
        # Setup
        mock_buses.__contains__ = Mock(return_value=True)
        mock_buses.__getitem__ = Mock(return_value=mock_can_bus)
        mock_buses.keys.return_value = ["vcan0"]
        mock_queue.put = AsyncMock()
        mock_queue.qsize.return_value = 1
        mock_queue.maxsize = 100

        # Test the complete flow
        interfaces = await can_service.get_interfaces()
        assert "vcan0" in interfaces

        # Send a message
        result = await can_service.send_raw_message(0x18EEFF00, b"\x01\x02", "vcan0")
        assert result["status"] == "queued"

        # Check queue status
        status = await can_service.get_queue_status()
        assert status["length"] == 1
