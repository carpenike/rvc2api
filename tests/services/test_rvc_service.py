#!/usr/bin/env python3
"""
Tests for RVC Service.

This module contains comprehensive tests for the RVCService class,
including initialization, lifecycle management, message processing,
and instance mapping functionality.
"""

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from backend.core.state import AppState
from backend.services.rvc_service import RVCService


class TestRVCService:
    """Test class for RVCService."""

    @pytest.fixture
    def mock_app_state(self) -> AppState:
        """Create a mock AppState for testing."""
        return MagicMock(spec=AppState)

    @pytest.fixture
    def rvc_service(self, mock_app_state: AppState) -> RVCService:
        """Create an RVCService instance for testing."""
        return RVCService(mock_app_state)

    def test_init(self, mock_app_state: AppState) -> None:
        """Test RVC service initialization."""
        service = RVCService(mock_app_state)

        assert service.app_state is mock_app_state
        assert service._running is False
        assert service._processing_task is None
        assert service._instance_mapping == {}
        assert service._message_handlers == {}

    @pytest.mark.asyncio
    async def test_start_service(self, rvc_service: RVCService) -> None:
        """Test starting the RVC service."""
        with patch("asyncio.create_task") as mock_create_task:
            mock_task = MagicMock()
            mock_create_task.return_value = mock_task

            await rvc_service.start()

            assert rvc_service._running is True
            assert rvc_service._processing_task is mock_task
            mock_create_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_service_already_running(self, rvc_service: RVCService) -> None:
        """Test starting service when already running."""
        rvc_service._running = True

        with patch("asyncio.create_task") as mock_create_task:
            await rvc_service.start()

            # Should not create new task if already running
            mock_create_task.assert_not_called()

    @pytest.mark.asyncio
    async def test_start_service_task_creation_fails(self, rvc_service: RVCService) -> None:
        """Test service start when task creation fails."""
        with patch("asyncio.create_task", side_effect=RuntimeError("Task creation failed")):
            with pytest.raises(RuntimeError, match="Task creation failed"):
                await rvc_service.start()

            # Service should not be marked as running if task creation fails
            assert rvc_service._running is False
            assert rvc_service._processing_task is None

    @pytest.mark.asyncio
    async def test_stop_service(self, rvc_service: RVCService) -> None:
        """Test stopping the RVC service."""

        # Create a real completed task for testing
        async def dummy_task():
            pass

        task = asyncio.create_task(dummy_task())
        await task  # Complete the task immediately

        rvc_service._running = True
        rvc_service._processing_task = task

        await rvc_service.stop()

        assert rvc_service._running is False
        assert rvc_service._processing_task is None

    @pytest.mark.asyncio
    async def test_stop_service_not_running(self, rvc_service: RVCService) -> None:
        """Test stopping service when not running."""
        await rvc_service.stop()

        # Should handle gracefully when not running
        assert rvc_service._running is False
        assert rvc_service._processing_task is None

    @pytest.mark.asyncio
    async def test_stop_service_with_cancelled_task(self, rvc_service: RVCService) -> None:
        """Test stopping service when task is cancelled."""

        # Create a real completed task for testing
        async def dummy_task():
            pass

        task = asyncio.create_task(dummy_task())
        await task  # Complete the task immediately

        rvc_service._running = True
        rvc_service._processing_task = task

        await rvc_service.stop()

        assert rvc_service._running is False
        assert rvc_service._processing_task is None

    @pytest.mark.asyncio
    async def test_process_messages_loop(self, rvc_service: RVCService) -> None:
        """Test the message processing loop."""
        rvc_service._running = True

        # Mock sleep to control loop iterations
        with patch("asyncio.sleep") as mock_sleep:
            # Set up to stop after 3 iterations
            call_count = 0

            async def side_effect(duration):
                nonlocal call_count
                call_count += 1
                if call_count >= 3:
                    rvc_service._running = False

            mock_sleep.side_effect = side_effect

            await rvc_service._process_messages()

            # Should have called sleep at least 3 times
            assert mock_sleep.call_count >= 3

    @pytest.mark.asyncio
    async def test_process_messages_cancelled(self, rvc_service: RVCService) -> None:
        """Test message processing when task is cancelled."""
        rvc_service._running = True

        with (
            patch("asyncio.sleep", side_effect=asyncio.CancelledError()),
            pytest.raises(asyncio.CancelledError),
        ):
            await rvc_service._process_messages()

    @pytest.mark.asyncio
    async def test_process_messages_exception_handling(self, rvc_service: RVCService) -> None:
        """Test message processing exception handling."""
        rvc_service._running = True

        with patch("asyncio.sleep", side_effect=RuntimeError("Processing error")):
            # Should not raise the exception, should log it instead
            await rvc_service._process_messages()

    def test_decode_message_not_implemented(self, rvc_service: RVCService) -> None:
        """Test message decoding (currently returns None)."""
        result = rvc_service.decode_message(0x1FFFF, b"\x01\x02\x03", 0x80)

        # Currently not implemented, should return None
        assert result is None

    def test_get_instance_name_no_mapping(self, rvc_service: RVCService) -> None:
        """Test getting instance name when no mapping exists."""
        name = rvc_service.get_instance_name(0x1FFFF, 1)

        assert name == "Instance 1"

    def test_get_instance_name_with_mapping(self, rvc_service: RVCService) -> None:
        """Test getting instance name with existing mapping."""
        # Register an instance name
        rvc_service.register_instance_name(0x1FFFF, 1, "Main Engine")

        name = rvc_service.get_instance_name(0x1FFFF, 1)

        assert name == "Main Engine"

    def test_get_instance_name_dgn_exists_instance_missing(self, rvc_service: RVCService) -> None:
        """Test getting instance name when DGN exists but instance doesn't."""
        # Register one instance
        rvc_service.register_instance_name(0x1FFFF, 1, "Main Engine")

        # Try to get a different instance
        name = rvc_service.get_instance_name(0x1FFFF, 2)

        assert name == "Instance 2"

    def test_register_instance_name(self, rvc_service: RVCService) -> None:
        """Test registering instance names."""
        rvc_service.register_instance_name(0x1FFFF, 1, "Main Engine")
        rvc_service.register_instance_name(0x1FFFF, 2, "Generator")
        rvc_service.register_instance_name(0x2FFFF, 1, "Water Tank")

        assert rvc_service._instance_mapping["131071"][1] == "Main Engine"
        assert rvc_service._instance_mapping["131071"][2] == "Generator"
        assert rvc_service._instance_mapping["196607"][1] == "Water Tank"

    def test_register_instance_name_overwrite(self, rvc_service: RVCService) -> None:
        """Test overwriting existing instance name."""
        rvc_service.register_instance_name(0x1FFFF, 1, "Main Engine")
        rvc_service.register_instance_name(0x1FFFF, 1, "Primary Engine")

        name = rvc_service.get_instance_name(0x1FFFF, 1)
        assert name == "Primary Engine"

    def test_init_message_handlers(self, rvc_service: RVCService) -> None:
        """Test message handlers initialization."""
        # Call the private method directly
        rvc_service._init_message_handlers()

        # Currently a placeholder, should not crash
        # In the future, this would verify specific handlers are registered
        assert isinstance(rvc_service._message_handlers, dict)

    @pytest.mark.asyncio
    async def test_full_lifecycle(self, rvc_service: RVCService) -> None:
        """Test complete service lifecycle: start -> register instances -> stop."""

        # Patch create_task to return a real, running task
        with patch("asyncio.create_task") as mock_create_task:
            # Dummy task that runs until cancelled
            async def dummy_task():
                try:
                    while True:
                        await asyncio.sleep(0.1)
                except asyncio.CancelledError:
                    pass

            task = asyncio.create_task(dummy_task())
            mock_create_task.return_value = task

            await rvc_service.start()
            assert rvc_service._running is True

            # Register some instance names
            rvc_service.register_instance_name(0x1FFFF, 1, "Main Engine")
            rvc_service.register_instance_name(0x1FFFF, 2, "Generator")

            # Verify instance names
            assert rvc_service.get_instance_name(0x1FFFF, 1) == "Main Engine"
            assert rvc_service.get_instance_name(0x1FFFF, 2) == "Generator"

            # Stop service (should cancel and await the dummy task)
            await rvc_service.stop()
            assert rvc_service._running is False
            assert rvc_service._processing_task is None

    def test_instance_mapping_persistence(self, rvc_service: RVCService) -> None:
        """Test that instance mappings persist across operations."""
        # Register multiple instances
        rvc_service.register_instance_name(0x1FFFF, 1, "Engine 1")
        rvc_service.register_instance_name(0x1FFFF, 2, "Engine 2")
        rvc_service.register_instance_name(0x2FFFF, 1, "Tank 1")

        # Verify all mappings exist
        assert len(rvc_service._instance_mapping) == 2
        assert len(rvc_service._instance_mapping["131071"]) == 2
        assert len(rvc_service._instance_mapping["196607"]) == 1

        # Verify specific mappings
        assert rvc_service.get_instance_name(0x1FFFF, 1) == "Engine 1"
        assert rvc_service.get_instance_name(0x1FFFF, 2) == "Engine 2"
        assert rvc_service.get_instance_name(0x2FFFF, 1) == "Tank 1"
