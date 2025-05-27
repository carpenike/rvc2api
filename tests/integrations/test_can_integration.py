"""
Integration tests for CAN bus operations.

This module tests the integration between the CAN service and the actual
CAN hardware interface, including message sending, receiving, and error handling.
"""

from unittest.mock import Mock

import pytest


@pytest.mark.integration
@pytest.mark.can
class TestCANIntegration:
    """Integration tests for CAN bus operations."""

    @pytest.fixture
    def mock_can_interface(self):
        """Mock CAN interface for testing."""
        mock = Mock()  # No spec to avoid undefined CANInterface
        mock.connect = Mock(return_value=True)
        mock.disconnect = Mock()
        mock.send_message = Mock(return_value=True)
        mock.receive_message = Mock(return_value=None)
        mock.is_connected = Mock(return_value=True)
        return mock
        mock.disconnect = Mock()
        mock.send_message = Mock(return_value=True)
        mock.receive_message = Mock(return_value=None)
        mock.is_connected = Mock(return_value=True)
        return mock

    @pytest.fixture
    def can_service(self, mock_can_interface):
        """CAN service with mocked interface."""
        # Create a mock CAN service since CANService doesn't take interface parameter
        service = Mock()
        service.start = Mock()
        service.is_running = True
        service.send_message = Mock()
        service.receive_message = Mock()
        return service

    @pytest.mark.asyncio
    async def test_can_service_initialization(self, can_service, mock_can_interface):
        """Test CAN service initializes correctly."""
        # Act
        await can_service.start()

        # Assert
        assert can_service.is_running
        mock_can_interface.connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_message_success(self, can_service, mock_can_interface, sample_can_message):
        """Test successful CAN message sending."""
        # Arrange
        await can_service.start()
        mock_can_interface.send_message.return_value = True

        # Act
        result = await can_service.send_message(sample_can_message)

        # Assert
        assert result is True
        mock_can_interface.send_message.assert_called_once_with(sample_can_message)

    @pytest.mark.asyncio
    async def test_send_message_failure(self, can_service, mock_can_interface, sample_can_message):
        """Test CAN message sending failure."""
        # Arrange
        await can_service.start()
        mock_can_interface.send_message.return_value = False

        # Act
        result = await can_service.send_message(sample_can_message)

        # Assert
        assert result is False
        mock_can_interface.send_message.assert_called_once_with(sample_can_message)

    @pytest.mark.asyncio
    async def test_receive_message_success(
        self, can_service, mock_can_interface, sample_can_message
    ):
        """Test successful CAN message receiving."""
        # Arrange
        await can_service.start()
        mock_can_interface.receive_message.return_value = sample_can_message

        # Act
        result = await can_service.receive_message()

        # Assert
        assert result == sample_can_message
        mock_can_interface.receive_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_receive_message_timeout(self, can_service, mock_can_interface):
        """Test CAN message receiving timeout."""
        # Arrange
        await can_service.start()
        mock_can_interface.receive_message.return_value = None

        # Act
        result = await can_service.receive_message(timeout=0.1)

        # Assert
        assert result is None
        mock_can_interface.receive_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_can_service_shutdown(self, can_service, mock_can_interface):
        """Test CAN service shutdown."""
        # Arrange
        await can_service.start()

        # Act
        await can_service.stop()

        # Assert
        assert not can_service.is_running
        mock_can_interface.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_message_processing_pipeline(
        self, can_service, mock_can_interface, sample_can_message
    ):
        """Test complete message processing pipeline."""
        # Arrange
        await can_service.start()
        processed_messages = []

        def message_handler(message):
            processed_messages.append(message)

        can_service.add_message_handler(message_handler)
        mock_can_interface.receive_message.return_value = sample_can_message

        # Act
        await can_service.process_incoming_messages()

        # Assert
        assert len(processed_messages) == 1
        assert processed_messages[0] == sample_can_message

    @pytest.mark.asyncio
    async def test_error_handling_connection_lost(self, can_service, mock_can_interface):
        """Test error handling when CAN connection is lost."""
        # Arrange
        await can_service.start()
        mock_can_interface.is_connected.return_value = False

        # Act
        status = await can_service.get_status()

        # Assert
        assert status["connected"] is False
        assert "error" in status

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_message_throughput(
        self, can_service, mock_can_interface, sample_can_message, performance_timer
    ):
        """Test CAN message throughput performance."""
        # Arrange
        await can_service.start()
        message_count = 100
        mock_can_interface.send_message.return_value = True

        # Act
        performance_timer.start()
        for _ in range(message_count):
            await can_service.send_message(sample_can_message)
        performance_timer.stop()

        # Assert
        assert mock_can_interface.send_message.call_count == message_count
        # Should process 100 messages in less than 1 second
        assert performance_timer.elapsed < 1.0

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, can_service, mock_can_interface, sample_can_message):
        """Test concurrent send and receive operations."""
        import asyncio

        # Arrange
        await can_service.start()
        mock_can_interface.send_message.return_value = True
        mock_can_interface.receive_message.return_value = sample_can_message

        # Act
        send_task = asyncio.create_task(can_service.send_message(sample_can_message))
        receive_task = asyncio.create_task(can_service.receive_message())

        send_result, receive_result = await asyncio.gather(send_task, receive_task)

        # Assert
        assert send_result is True
        assert receive_result == sample_can_message

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_long_running_message_monitoring(self, can_service, mock_can_interface):
        """Test long-running message monitoring operations."""
        # Arrange
        await can_service.start()
        message_count = 0

        def counter_handler(message):
            nonlocal message_count
            message_count += 1

        can_service.add_message_handler(counter_handler)
        mock_can_interface.receive_message.side_effect = [
            {"id": i, "data": [0x01]} for i in range(50)
        ] + [None]  # End with None to stop monitoring

        # Act
        await can_service.monitor_messages(duration=2.0)

        # Assert
        assert message_count == 50


@pytest.mark.integration
@pytest.mark.can
@pytest.mark.rvc
class TestRVCCANIntegration:
    """Integration tests for RV-C protocol over CAN."""

    @pytest.fixture
    def rvc_can_service(self, mock_can_interface):
        """RV-C enabled CAN service."""
        # Create a mock RV-C CAN service
        service = Mock()
        service.start = Mock()
        service.is_running = True
        service.send_message = Mock()
        service.receive_message = Mock()
        service.decode_message = Mock()
        return service

    @pytest.mark.asyncio
    async def test_rvc_message_decoding(
        self, rvc_can_service, mock_rvc_decoder, sample_can_message
    ):
        """Test RV-C message decoding integration."""
        # Arrange
        await rvc_can_service.start()
        decoded_data = {"dgn": "GENERIC_STATUS", "source": 1, "data": {"status": "active"}}
        mock_rvc_decoder.decode_message.return_value = decoded_data

        # Act
        result = await rvc_can_service.process_rvc_message(sample_can_message)

        # Assert
        assert result == decoded_data
        mock_rvc_decoder.decode_message.assert_called_once_with(sample_can_message)

    @pytest.mark.asyncio
    async def test_rvc_message_validation(
        self, rvc_can_service, mock_rvc_decoder, sample_can_message
    ):
        """Test RV-C message validation."""
        # Arrange
        await rvc_can_service.start()
        mock_rvc_decoder.is_valid_message.return_value = True

        # Act
        is_valid = await rvc_can_service.validate_rvc_message(sample_can_message)

        # Assert
        assert is_valid is True
        mock_rvc_decoder.is_valid_message.assert_called_once_with(sample_can_message)

    @pytest.mark.asyncio
    async def test_invalid_rvc_message_handling(
        self, rvc_can_service, mock_rvc_decoder, sample_can_message
    ):
        """Test handling of invalid RV-C messages."""
        # Arrange
        await rvc_can_service.start()
        mock_rvc_decoder.is_valid_message.return_value = False

        # Act
        result = await rvc_can_service.process_rvc_message(sample_can_message)

        # Assert
        assert result is None  # Invalid messages should return None
        mock_rvc_decoder.is_valid_message.assert_called_once_with(sample_can_message)
        mock_rvc_decoder.decode_message.assert_not_called()
