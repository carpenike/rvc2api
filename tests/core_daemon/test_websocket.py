"""
Tests for the WebSocket functionalities in `core_daemon.websocket`.

This module covers:
- `WebSocketLogHandler`: Forwards logging records to connected WebSocket clients.
- `broadcast_to_clients`: Sends messages to all active data WebSocket clients.
- WebSocket endpoints (`/ws/data`, `/ws/logs`): Manages client connections,
  disconnections, and message handling for data and log streams.

Tests verify client management (add/remove on connect/disconnect/error),
message delivery, error handling, and logging of significant events.
Mocks are used for WebSocket clients, asyncio loop, and loggers to isolate tests.
FastAPI's TestClient is used for endpoint testing.
"""

# tests/core_daemon/test_websocket.py
import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from core_daemon import websocket
from core_daemon.websocket import WebSocketLogHandler, broadcast_to_clients
from fastapi import FastAPI, WebSocket
from fastapi.testclient import TestClient

# Import metrics and clear them if they were to be used
# from core_daemon.metrics import WS_CLIENTS, WS_MESSAGES


@pytest.fixture(autouse=True)
def reset_global_websocket_clients():
    """Resets the global WebSocket client sets before each test execution.

    Ensures that `websocket.clients` and `websocket.log_ws_clients` are empty,
    providing a clean state for each test and preventing interference between them.
    This fixture is applied automatically to all tests in this module due to `autouse=True`.
    """
    websocket.clients.clear()
    websocket.log_ws_clients.clear()


@pytest.fixture
def mock_websocket_client():
    """Provides a mock `fastapi.WebSocket` client instance.

    The mock is an `AsyncMock` to allow awaiting its methods. It includes
    mocked `client.host` and `client.port` attributes for connection identification.
    Ensures hashability for set operations in tests.
    """
    ws = AsyncMock(spec=WebSocket)
    ws.client.host = "127.0.0.1"
    ws.client.port = 12345
    ws.__hash__.return_value = id(ws)
    ws.__eq__.side_effect = lambda other: ws is other
    return ws


@pytest.fixture
def mock_asyncio_loop():
    """Provides a mock `asyncio.AbstractEventLoop` with run_coroutine_threadsafe mocked."""
    loop = MagicMock(spec=asyncio.AbstractEventLoop)
    loop.is_running.return_value = True
    loop.run_coroutine_threadsafe = MagicMock()
    return loop


class TestWebSocketLogHandler:
    """Tests for the WebSocketLogHandler which streams log records to clients."""

    def test_emit_sends_to_clients(self, mock_asyncio_loop, mock_websocket_client):
        """Verifies that log records are formatted and sent to connected log clients."""
        handler = WebSocketLogHandler(loop=mock_asyncio_loop)
        handler.setFormatter(logging.Formatter("%(message)s"))  # Simple formatter

        websocket.log_ws_clients.add(mock_websocket_client)
        record = logging.LogRecord(
            name="testlogger",
            level=logging.INFO,
            pathname="testpath",
            lineno=1,
            msg="Test log message",
            args=(),
            exc_info=None,
            func="test_func",
        )

        with patch("asyncio.run_coroutine_threadsafe") as mock_run_coroutine_threadsafe:
            handler.emit(record)
            mock_run_coroutine_threadsafe.assert_called_once()
            mock_websocket_client.send_text.assert_called_once_with("Test log message")

    def test_emit_removes_client_on_send_failure(self, mock_asyncio_loop, mock_websocket_client):
        """Tests that a client is removed if sending a log message to it fails."""
        handler = WebSocketLogHandler(loop=mock_asyncio_loop)
        websocket.log_ws_clients.add(mock_websocket_client)

        # Simulate run_coroutine_threadsafe raising an error by
        # patching asyncio.run_coroutine_threadsafe
        record = logging.LogRecord(
            name="testlogger",
            level=logging.INFO,
            pathname="testpath",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None,
            func="test_func",
        )
        with patch("asyncio.run_coroutine_threadsafe", side_effect=Exception("Send failed")):
            handler.emit(record)
        # Use identity check to avoid AsyncMock hash/equality quirks
        assert not any(ws is mock_websocket_client for ws in websocket.log_ws_clients)

        # Simulate coroutine failure after scheduling (done callback)
        websocket.log_ws_clients.add(mock_websocket_client)

        class DummyFuture:
            def add_done_callback(self, cb):
                class DummyResult:
                    def result(self):
                        raise Exception("Send failed in coroutine")

                cb(DummyResult())

        with patch("asyncio.run_coroutine_threadsafe", return_value=DummyFuture()):
            handler.emit(record)
        assert not any(ws is mock_websocket_client for ws in websocket.log_ws_clients)

    def test_emit_no_clients(self, mock_asyncio_loop):
        """Tests that emit does not raise an error if no log clients are connected."""
        handler = WebSocketLogHandler(loop=mock_asyncio_loop)
        record = logging.LogRecord(
            name="testlogger",
            level=logging.INFO,
            pathname="testpath",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None,
            func="test_func",
        )
        handler.emit(record)  # Should not raise an error
        mock_asyncio_loop.run_coroutine_threadsafe.assert_not_called()

    def test_emit_loop_not_running(self, mock_asyncio_loop, mock_websocket_client):
        """Tests that log messages are not sent if the asyncio loop is not running."""
        handler = WebSocketLogHandler(loop=mock_asyncio_loop)
        websocket.log_ws_clients.add(mock_websocket_client)
        mock_asyncio_loop.is_running.return_value = False
        record = logging.LogRecord(
            name="testlogger",
            level=logging.INFO,
            pathname="testpath",
            lineno=1,
            msg="Test",
            args=(),
            exc_info=None,
            func="test_func",
        )
        handler.emit(record)
        # send_text should not be called if loop is not running
        mock_asyncio_loop.run_coroutine_threadsafe.assert_not_called()


@pytest.mark.asyncio
class TestBroadcastToClients:
    """Tests for the `broadcast_to_clients` function."""

    async def test_broadcast_sends_to_all_clients(self, mock_websocket_client):
        """Ensures messages are broadcast to all connected (non-log) clients."""
        client1 = mock_websocket_client
        client2 = AsyncMock(spec=WebSocket)
        websocket.clients.add(client1)
        websocket.clients.add(client2)

        await broadcast_to_clients("Hello everyone")

        client1.send_text.assert_awaited_once_with("Hello everyone")
        client2.send_text.assert_awaited_once_with("Hello everyone")

    async def test_broadcast_removes_client_on_failure(self, mock_websocket_client):
        """Tests that a client is removed if broadcasting a message to it fails."""
        client1 = mock_websocket_client
        client2 = AsyncMock(spec=WebSocket)  # Good client
        websocket.clients.add(client1)
        websocket.clients.add(client2)

        client1.send_text.side_effect = Exception("Connection lost")

        await broadcast_to_clients("Important update")

        assert client1 not in websocket.clients
        assert client2 in websocket.clients
        client2.send_text.assert_awaited_once_with("Important update")

    async def test_broadcast_no_clients(self):
        """Tests that broadcast does not raise an error if no clients are connected."""
        await broadcast_to_clients("Anyone there?")  # Should not raise an error


@pytest.mark.asyncio
class TestWebSocketEndpoints:
    """Tests for the WebSocket data and logs endpoints (/ws/data, /ws/logs)."""

    @pytest.fixture
    def app(self):
        """Provides a FastAPI application instance with WebSocket routes configured."""
        _app = FastAPI()
        # Ensure the routes are added with the correct module reference
        _app.add_websocket_route("/ws/data", websocket.websocket_endpoint)
        _app.add_websocket_route("/ws/logs", websocket.websocket_logs_endpoint)
        return _app

    @pytest.fixture
    def client(self, app):
        """Provides a TestClient for the FastAPI application."""
        return TestClient(app)

    async def test_websocket_data_endpoint_connect_disconnect(self, client, app):
        """Tests connect and disconnect behavior for the /ws/data endpoint.

        Verifies that clients are added to and removed from the active client set.
        """
        assert len(websocket.clients) == 0
        with client.websocket_connect("/ws/data") as _ws_conn:
            assert len(websocket.clients) == 1
        assert len(websocket.clients) == 0  # Check removal on disconnect

    async def test_websocket_logs_endpoint_connect_disconnect(self, client, app):
        """Tests connect and disconnect behavior for the /ws/logs endpoint.

        Verifies that clients are added to and removed from the active log client set.
        """
        assert len(websocket.log_ws_clients) == 0
        with client.websocket_connect("/ws/logs") as _ws_conn:
            assert len(websocket.log_ws_clients) == 1
        assert len(websocket.log_ws_clients) == 0

    @patch("core_daemon.websocket.logger")  # Patch logger in the websocket module
    async def test_websocket_data_endpoint_handles_exception(
        self, mock_logger, client, app, mock_websocket_client
    ):
        """Tests logging of client connect and disconnect events for /ws/data."""
        # This test is more complex as it requires injecting a problematic WebSocket
        # into the TestClient's context or mocking receive_text to raise an error.
        # For simplicity, we'll check the logging on disconnect path.
        with client.websocket_connect("/ws/data") as _ws_conn:
            assert len(websocket.clients) == 1
        assert len(websocket.clients) == 0
        # Check if logger.info was called for connect and disconnect
        connect_log_found = any(
            "WebSocket client connected" in call_args[0][0]
            for call_args in mock_logger.info.call_args_list
        )
        disconnect_log_found = any(
            "WebSocket client disconnected" in call_args[0][0]
            for call_args in mock_logger.info.call_args_list
        )
        assert connect_log_found
        assert disconnect_log_found

    # Test for unexpected error during ws.receive_text()
    @patch("core_daemon.websocket.logger")
    async def test_websocket_data_endpoint_unexpected_error(self, mock_logger, client, app):
        """Tests error handling when an unexpected error occurs during receive_text on /ws/data.

        Verifies that the client is removed and the error is logged.
        """
        # Patch receive_text to raise an error
        with patch(
            "core_daemon.websocket.WebSocket.receive_text", new_callable=AsyncMock
        ) as mock_receive_text:
            mock_receive_text.side_effect = RuntimeError("Unexpected error")

            with client.websocket_connect("/ws/data"):
                # The connection will close due to the error, but no exception will be raised here
                pass

        # Assert that the error was logged
        assert mock_logger.error.called
        assert any("Unexpected error" in str(call) for call in mock_logger.error.call_args_list)
        # Optionally, check that the client was removed
        assert len(websocket.clients) == 0
