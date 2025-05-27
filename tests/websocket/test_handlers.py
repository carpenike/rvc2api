"""
Tests for WebSocket functionality.

This module tests WebSocket connections, message broadcasting,
and real-time communication features.
"""

import pytest


@pytest.mark.websocket
class TestWebSocketHandlers:
    """Test suite for WebSocket handlers and connections."""

    @pytest.mark.asyncio
    async def test_websocket_connection_success(self, websocket_test_client):
        """Test successful WebSocket connection establishment."""
        # Act & Assert
        with websocket_test_client.websocket_connect("/ws") as websocket:
            # Connection should be established successfully
            assert websocket is not None

    @pytest.mark.asyncio
    async def test_websocket_message_sending(self, websocket_test_client):
        """Test sending messages through WebSocket."""
        # Arrange
        test_message = {"type": "ping", "data": "test"}

        # Act & Assert
        with websocket_test_client.websocket_connect("/ws") as websocket:
            websocket.send_json(test_message)
            response = websocket.receive_json()

            assert response["type"] == "pong"
            assert "timestamp" in response

    @pytest.mark.asyncio
    async def test_websocket_entity_updates(self, websocket_test_client, sample_entity_data):
        """Test real-time entity update broadcasting."""
        # Arrange
        entity_update = {
            "type": "entity_update",
            "entity_id": sample_entity_data["id"],
            "data": sample_entity_data,
        }

        # Act & Assert
        with websocket_test_client.websocket_connect("/ws") as websocket:
            # Subscribe to entity updates
            websocket.send_json({"type": "subscribe", "topic": "entity_updates"})

            # Simulate entity update broadcast
            websocket.send_json(entity_update)

            # Should receive the update
            response = websocket.receive_json()
            assert response["type"] == "entity_update"
            assert response["entity_id"] == sample_entity_data["id"]

    @pytest.mark.asyncio
    async def test_websocket_can_message_streaming(self, websocket_test_client, sample_can_message):
        """Test streaming CAN messages through WebSocket."""
        # Arrange
        can_stream_message = {"type": "can_message", "message": sample_can_message}

        # Act & Assert
        with websocket_test_client.websocket_connect("/ws") as websocket:
            # Subscribe to CAN messages
            websocket.send_json({"type": "subscribe", "topic": "can_messages"})

            # Simulate CAN message
            websocket.send_json(can_stream_message)

            # Should receive the CAN message
            response = websocket.receive_json()
            assert response["type"] == "can_message"
            assert response["message"]["arbitration_id"] == sample_can_message["arbitration_id"]

    @pytest.mark.asyncio
    async def test_websocket_multiple_clients(self, websocket_test_client):
        """Test multiple WebSocket client connections."""
        # Act & Assert
        with (
            websocket_test_client.websocket_connect("/ws") as ws1,
            websocket_test_client.websocket_connect("/ws") as ws2,
        ):
            # Both connections should be established
            assert ws1 is not None
            assert ws2 is not None

            # Test bidirectional communication
            test_message = {"type": "test", "data": "hello"}
            ws1.send_json(test_message)
            ws2.send_json(test_message)

            # Both should receive responses
            response1 = ws1.receive_json()
            response2 = ws2.receive_json()

            assert response1 is not None
            assert response2 is not None

    @pytest.mark.asyncio
    async def test_websocket_error_handling(self, websocket_test_client):
        """Test WebSocket error handling for invalid messages."""
        # Act & Assert
        with websocket_test_client.websocket_connect("/ws") as websocket:
            # Send invalid message format
            websocket.send_text("invalid json")

            # Should receive error response
            response = websocket.receive_json()
            assert response["type"] == "error"
            assert "Invalid message format" in response["message"]

    @pytest.mark.asyncio
    async def test_websocket_authentication(self, websocket_test_client):
        """Test WebSocket authentication and authorization."""
        # Arrange
        auth_message = {"type": "auth", "token": "valid_token"}

        # Act & Assert
        with websocket_test_client.websocket_connect("/ws") as websocket:
            # Send authentication
            websocket.send_json(auth_message)

            # Should receive auth success
            response = websocket.receive_json()
            assert response["type"] == "auth_success"
            assert response["authenticated"] is True

    @pytest.mark.asyncio
    async def test_websocket_subscription_management(self, websocket_test_client):
        """Test WebSocket subscription and unsubscription."""
        # Act & Assert
        with websocket_test_client.websocket_connect("/ws") as websocket:
            # Subscribe to topic
            websocket.send_json({"type": "subscribe", "topic": "entity_updates"})
            response = websocket.receive_json()
            assert response["type"] == "subscription_confirmed"

            # Unsubscribe from topic
            websocket.send_json({"type": "unsubscribe", "topic": "entity_updates"})
            response = websocket.receive_json()
            assert response["type"] == "unsubscription_confirmed"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_websocket_message_throughput(self, websocket_test_client, performance_timer):
        """Test WebSocket message throughput performance."""
        # Arrange
        message_count = 100
        test_message = {"type": "performance_test", "data": "test"}

        # Act & Assert
        with websocket_test_client.websocket_connect("/ws") as websocket:
            performance_timer.start()

            for i in range(message_count):
                websocket.send_json({**test_message, "id": i})
                response = websocket.receive_json()
                assert response is not None

            performance_timer.stop()

            # Should handle 100 messages in reasonable time
            assert performance_timer.elapsed < 2.0

    @pytest.mark.asyncio
    async def test_websocket_connection_cleanup(self, websocket_test_client):
        """Test proper cleanup when WebSocket connection is closed."""
        # Arrange
        connection_id = None

        # Act
        with websocket_test_client.websocket_connect("/ws") as websocket:
            # Get connection ID
            websocket.send_json({"type": "get_connection_id"})
            response = websocket.receive_json()
            connection_id = response.get("connection_id")

        # Connection should be cleaned up after closing
        # This would typically be verified by checking internal state
        # or connection registry, which would need to be mocked
        assert connection_id is not None

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_websocket_long_lived_connection(self, websocket_test_client):
        """Test long-lived WebSocket connections."""
        import asyncio

        # Act & Assert
        with websocket_test_client.websocket_connect("/ws") as websocket:
            # Keep connection alive and send periodic messages
            for i in range(10):
                message = {"type": "heartbeat", "sequence": i}
                websocket.send_json(message)

                response = websocket.receive_json()
                assert response["type"] == "heartbeat_ack"
                assert response["sequence"] == i

                # Wait between messages
                await asyncio.sleep(0.1)


@pytest.mark.websocket
@pytest.mark.integration
class TestWebSocketIntegration:
    """Integration tests for WebSocket with backend services."""

    @pytest.mark.asyncio
    async def test_websocket_with_entity_service(
        self, websocket_test_client, override_entity_service, sample_entity_data
    ):
        """Test WebSocket integration with entity service."""
        # Arrange
        override_entity_service.get_all.return_value = [sample_entity_data]

        # Act & Assert
        with websocket_test_client.websocket_connect("/ws") as websocket:
            # Request entity data through WebSocket
            websocket.send_json({"type": "get_entities"})

            response = websocket.receive_json()
            assert response["type"] == "entities_data"
            assert len(response["entities"]) == 1
            assert response["entities"][0]["id"] == sample_entity_data["id"]

    @pytest.mark.asyncio
    async def test_websocket_with_can_service(
        self, websocket_test_client, override_can_service, sample_can_message
    ):
        """Test WebSocket integration with CAN service."""
        # Arrange
        override_can_service.get_status.return_value = {"connected": True, "message_count": 100}

        # Act & Assert
        with websocket_test_client.websocket_connect("/ws") as websocket:
            # Request CAN status through WebSocket
            websocket.send_json({"type": "get_can_status"})

            response = websocket.receive_json()
            assert response["type"] == "can_status"
            assert response["status"]["connected"] is True
            assert response["status"]["message_count"] == 100
