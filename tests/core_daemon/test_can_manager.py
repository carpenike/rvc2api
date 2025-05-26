"""
Unit tests for the can_manager module in the core_daemon.

These tests cover:
- Construction of CAN messages for light control.
- Initialization and management of CAN bus listeners using threads.
- The asynchronous CAN writer task responsible for sending messages from a queue.
- Error handling for CAN bus operations (initialization, sending).
"""

import asyncio
import os
from unittest.mock import MagicMock, patch

import can  # Import the 'can' module itself
import pytest
from can.exceptions import CanError, CanInterfaceNotImplementedError
from core_daemon import can_manager


# Reset relevant parts of can_manager before each test
@pytest.fixture(autouse=True)
def reset_can_manager_state():
    """
    Automatically used fixture to reset global state variables in can_manager
    (like the transmit queue and bus instances) before each test.
    """
    can_manager.can_tx_queue = asyncio.Queue()
    can_manager.buses = {}
    # If CAN_TX_QUEUE_LENGTH is a mockable object (e.g., MagicMock from Prometheus client)
    # you might want to reset its methods if they are called directly.
    # For this example, we'll assume it's a global object whose 'set' method is called.
    # If it needs more specific reset, that should be handled here.


@pytest.fixture
def mock_can_message():
    """Provides a standard can.Message object for use in tests."""
    return can.Message(arbitration_id=0x123, data=[1, 2, 3], is_extended_id=True)


# --- Tests for create_light_can_message ---


def test_create_light_can_message_pdu1():
    """
    Test create_light_can_message for a PDU1 type message (PF < 0xF0).
    Verifies correct arbitration ID and payload construction.
    """
    # PF < 0xF0 (e.g., PGN = 0xEF00) -> PDU1
    # PGN = 0xEF00 => PF = 0xEF, PS = 0x00
    # DP = 0 (assuming PGN < 0x10000)
    # Prio = 6, SA = 0xF9, DA = 0xFF
    # Expected ID: (6 << 26) | (0 << 24) | (0xEF << 16) | (0xFF << 8) | 0xF9
    #             : 0x18EF_FF_F9 (standard PDU1 format)
    pgn = 0xEF00  # Example PGN for PDU1
    instance = 1
    brightness_can_level = 100  # 0x64

    msg = can_manager.create_light_can_message(pgn, instance, brightness_can_level)

    assert msg.is_extended_id is True
    # Expected ID calculation:
    # prio = 6 (0b110), dp = 0 (pgn < 0x10000), pf = 0xEF, da = 0xFF, sa = 0xF9
    # id = (6<<26) | (0<<24) | (0xEF<<16) | (0xFF<<8) | 0xF9 = 0x18EFFF9
    assert msg.arbitration_id == 0x18EFFF9
    expected_payload = bytes(
        [
            instance,  # Instance
            0x7C,  # Group Mask
            brightness_can_level,  # Level
            0x00,  # Command: SetLevel
            0x00,  # Duration: Instantaneous
            0xFF,  # Reserved
            0xFF,  # Reserved
            0xFF,  # Reserved
        ]
    )
    assert msg.data == expected_payload


def test_create_light_can_message_pdu2():
    """
    Test create_light_can_message for a PDU2 type message (PF >= 0xF0).
    Verifies correct arbitration ID and payload construction.
    """
    # PF >= 0xF0 (e.g., PGN = 0x1F0D0) -> PDU2
    # PGN = 0x1F0D0 => PF = 0xF0, PS = 0xD0 (Group Extension)
    # DP = 1 (pgn >= 0x10000)
    # Prio = 6, SA = 0xF9
    # Expected ID: (6 << 26) | (1 << 24) | (0xF0 << 16) | (0xD0 << 8) | 0xF9
    #             : 0x19F0_D0_F9 (standard PDU2 format)
    pgn = 0x1F0D0  # Example PGN for PDU2 (DML_COMMAND_2)
    instance = 2
    brightness_can_level = 200  # 0xC8

    msg = can_manager.create_light_can_message(pgn, instance, brightness_can_level)

    assert msg.is_extended_id is True
    # Expected ID calculation:
    # prio = 6, dp = 1 (pgn >= 0x10000), pf = 0xF0, ps = 0xD0, sa = 0xF9
    # id = (6<<26) | (1<<24) | (0xF0<<16) | (0xD0<<8) | 0xF9 = 0x19F0D0F9
    assert msg.arbitration_id == 0x19F0D0F9
    expected_payload = bytes(
        [
            instance,  # Instance
            0x7C,  # Group Mask
            brightness_can_level,  # Level
            0x00,  # Command: SetLevel
            0x00,  # Duration: Instantaneous
            0xFF,  # Reserved
            0xFF,  # Reserved
            0xFF,  # Reserved
        ]
    )
    assert msg.data == expected_payload


# --- Tests for initialize_can_listeners ---


@patch("can.interface.Bus")
@patch("threading.Thread")
def test_initialize_can_listeners_success(mock_thread_cls, mock_bus_cls):
    """
    Test successful initialization of CAN listeners for multiple interfaces.
    Ensures buses are created, threads are started, and logs are appropriate.
    """
    mock_logger = MagicMock(spec=["info", "warning", "error"])
    mock_handler_callback = MagicMock()
    interfaces = ["can0", "can1"]
    bustype = "socketcan"
    bitrate = 500000

    mock_bus_instance_can0 = MagicMock(spec=can.Bus)
    mock_bus_instance_can1 = MagicMock(spec=can.Bus)
    mock_bus_cls.side_effect = [mock_bus_instance_can0, mock_bus_instance_can1]

    mock_thread_instance = MagicMock()
    mock_thread_cls.return_value = mock_thread_instance

    can_manager.initialize_can_listeners(
        interfaces, bustype, bitrate, mock_handler_callback, mock_logger
    )

    assert mock_bus_cls.call_count == 2
    mock_bus_cls.assert_any_call(channel="can0", bustype=bustype, bitrate=bitrate)
    mock_bus_cls.assert_any_call(channel="can1", bustype=bustype, bitrate=bitrate)

    assert can_manager.buses["can0"] == mock_bus_instance_can0
    assert can_manager.buses["can1"] == mock_bus_instance_can1

    assert mock_thread_cls.call_count == 2
    # Check that Thread was called with target=reader_thread_target and correct args
    # This is a bit more involved as reader_thread_target is an inner function.
    # We can check the args passed to Thread constructor.
    thread_args_calls = [args[1] for args in mock_thread_cls.call_args_list]
    assert ("can0",) in thread_args_calls
    assert ("can1",) in thread_args_calls

    mock_thread_instance.start.assert_called()
    assert mock_thread_instance.start.call_count == 2
    mock_logger.info.assert_any_call(f"{len(interfaces)} CAN listener(s) initialized and started.")


def test_initialize_can_listeners_no_interfaces():
    """Test initialize_can_listeners when no interfaces are specified."""
    mock_logger = MagicMock(spec=["info", "warning", "error"])
    can_manager.initialize_can_listeners([], "socketcan", 250000, MagicMock(), mock_logger)
    mock_logger.warning.assert_called_once_with(
        "No CAN interfaces specified. CAN listeners will not be started."
    )


@patch("can.interface.Bus", side_effect=CanInterfaceNotImplementedError("Test Error"))
@patch("threading.Thread")  # Still need to patch Thread, though it won't be used if Bus fails
def test_initialize_can_listeners_bus_init_not_implemented_error(mock_thread_cls, mock_bus_cls):
    """
    Test initialize_can_listeners when can.interface.Bus raises CanInterfaceNotImplementedError.
    Ensures the error is logged and no thread is started for the failed bus.
    """
    mock_logger = MagicMock(spec=["info", "warning", "error"])
    interfaces = ["can0"]
    can_manager.initialize_can_listeners(
        interfaces, "nonexistent", 250000, MagicMock(), mock_logger
    )
    mock_bus_cls.assert_called_once_with(channel="can0", bustype="nonexistent", bitrate=250000)
    mock_logger.error.assert_called_once_with(
        "Cannot open CAN bus 'can0' (nonexistent, 250000bps): Test Error"
    )
    assert "can0" not in can_manager.buses
    mock_thread_cls.assert_not_called()  # Thread should not be started if bus fails


@patch("can.interface.Bus", side_effect=Exception("Generic Bus Error"))
@patch("threading.Thread")
def test_initialize_can_listeners_bus_init_generic_exception(mock_thread_cls, mock_bus_cls):
    """
    Test initialize_can_listeners when can.interface.Bus raises a generic exception.
    Ensures the error is logged and no thread is started for the failed bus.
    """
    mock_logger = MagicMock(spec=["info", "warning", "error"])
    interfaces = ["can0"]
    can_manager.initialize_can_listeners(interfaces, "socketcan", 250000, MagicMock(), mock_logger)
    mock_bus_cls.assert_called_once_with(channel="can0", bustype="socketcan", bitrate=250000)
    mock_logger.error.assert_called_once_with(
        "Failed to initialize CAN bus 'can0' (socketcan, "
        "250000bps) due to an unexpected error: Generic Bus Error"
    )
    assert "can0" not in can_manager.buses
    mock_thread_cls.assert_not_called()


# Test for the reader_thread_target inner function is more complex
# It would involve stopping the thread or mocking time.sleep and bus.recv
# For now, we assume the logic within reader_thread_target is correct if initialize_can_listeners
# sets it up correctly. A more direct test of reader_thread_target might be needed
# if its logic becomes more complex.

# --- Tests for can_writer ---


@pytest.mark.asyncio
@patch("core_daemon.can_manager.CAN_TX_QUEUE_LENGTH")  # Mock the metric object
@patch("can.interface.Bus")  # Mock the Bus class from the 'can' library
async def test_can_writer_sends_message_bus_exists(
    mock_bus_cls, mock_metric_gauge, mock_can_message
):
    """
    Test the can_writer successfully sends a message when the bus instance already exists.
    Verifies the message is sent and metrics are updated.
    """
    # This test focuses on the scenario where the bus is already in can_manager.buses
    mock_bus_instance = MagicMock(spec=can.Bus)  # Instance of a CAN bus
    mock_bus_instance.send = MagicMock()  # Mock the send method

    interface_name = "can0"
    can_manager.buses[interface_name] = mock_bus_instance

    # Put a message on the queue
    await can_manager.can_tx_queue.put((mock_can_message, interface_name))
    # Add a sentinel to stop the writer after one message for testing
    await can_manager.can_tx_queue.put((None, None))  # Sentinel to break loop

    # Create a task for can_writer and wait for it to process the one message
    writer_task = asyncio.create_task(can_manager.can_writer())

    # Allow the writer to run. The timeout ensures the test doesn't hang if something is wrong.
    try:
        await asyncio.wait_for(writer_task, timeout=1.0)
    except TimeoutError:
        pytest.fail("can_writer task timed out")
    except RuntimeError as e:  # Catch the sentinel
        if "NoneType" not in str(e):  # Reraise if not our sentinel
            raise

    # Assertions
    assert mock_bus_instance.send.call_count == 2  # Called twice
    mock_bus_instance.send.assert_called_with(mock_can_message)
    # Metric assertions
    # Called after get, after task_done. Initial qsize 1, then 0.
    # If sentinel is used, it might be called for that too.
    # Let's check the sequence of calls if possible or at least the final state.
    # For simplicity, check it was called. More specific checks might be needed.
    mock_metric_gauge.set.assert_called()


@pytest.mark.asyncio
@patch("core_daemon.can_manager.CAN_TX_QUEUE_LENGTH")
@patch("can.interface.Bus")  # Mocking the class
async def test_can_writer_initializes_bus_if_not_exists(
    mock_bus_cls, mock_metric_gauge, mock_can_message
):
    """
    Test the can_writer initializes a new bus instance if it's not already cached.
    Verifies bus creation, message sending, and metric updates.
    """
    mock_new_bus_instance = MagicMock(spec=can.Bus)
    mock_new_bus_instance.send = MagicMock()
    mock_bus_cls.return_value = mock_new_bus_instance  # When can.interface.Bus() is called

    interface_name = "can1"
    # Ensure bus is NOT in can_manager.buses
    assert interface_name not in can_manager.buses

    os.environ["CAN_BUSTYPE"] = "test_bustype"  # For the fallback initialization

    await can_manager.can_tx_queue.put((mock_can_message, interface_name))
    await can_manager.can_tx_queue.put((None, None))  # Sentinel

    writer_task = asyncio.create_task(can_manager.can_writer())
    try:
        await asyncio.wait_for(writer_task, timeout=1.0)
    except TimeoutError:
        pytest.fail("can_writer task timed out during bus initialization test")
    except RuntimeError as e:  # Catch the sentinel
        if "NoneType" not in str(e):
            raise

    mock_bus_cls.assert_called_once_with(channel=interface_name, bustype="test_bustype")
    assert can_manager.buses[interface_name] == mock_new_bus_instance
    assert mock_new_bus_instance.send.call_count == 2
    mock_new_bus_instance.send.assert_called_with(mock_can_message)
    mock_metric_gauge.set.assert_called()
    del os.environ["CAN_BUSTYPE"]  # Clean up env var


@pytest.mark.asyncio
@patch("core_daemon.can_manager.CAN_TX_QUEUE_LENGTH")
@patch("can.interface.Bus")
async def test_can_writer_handles_can_error_on_send(
    mock_bus_cls, mock_metric_gauge, mock_can_message
):
    """
    Test the can_writer handles CanError exceptions during message sending.
    Ensures the error is logged and the writer continues.
    """
    mock_bus_instance = MagicMock(spec=can.Bus)
    mock_bus_instance.send.side_effect = CanError("Send failed")
    interface_name = "can0"
    can_manager.buses[interface_name] = mock_bus_instance

    await can_manager.can_tx_queue.put((mock_can_message, interface_name))
    await can_manager.can_tx_queue.put((None, None))  # Sentinel

    with patch.object(can_manager.logger, "error") as mock_logger_error:
        writer_task = asyncio.create_task(can_manager.can_writer())
        try:
            await asyncio.wait_for(writer_task, timeout=1.0)
        except TimeoutError:
            pytest.fail("can_writer task timed out during CanError test")
        except RuntimeError as e:  # Catch the sentinel
            if "NoneType" not in str(e):
                raise

        mock_bus_instance.send.assert_called_once_with(
            mock_can_message
        )  # Attempted once before error
        mock_logger_error.assert_any_call(
            f"CAN writer failed to send message on {interface_name}: Send failed"
        )
    mock_metric_gauge.set.assert_called()


@pytest.mark.asyncio
@patch("core_daemon.can_manager.CAN_TX_QUEUE_LENGTH")
@patch("can.interface.Bus", side_effect=CanInterfaceNotImplementedError("Init failed"))
async def test_can_writer_handles_bus_init_error_fallback(
    mock_bus_cls, mock_metric_gauge, mock_can_message
):
    """
    Test the can_writer handles errors during the fallback bus initialization.
    Ensures the error is logged and the bus is not added to the cache.
    """
    interface_name = "can_uninit"
    os.environ["CAN_BUSTYPE"] = "failing_bustype"

    await can_manager.can_tx_queue.put((mock_can_message, interface_name))
    await can_manager.can_tx_queue.put((None, None))  # Sentinel

    with patch.object(can_manager.logger, "error") as mock_logger_error:
        writer_task = asyncio.create_task(can_manager.can_writer())
        try:
            await asyncio.wait_for(writer_task, timeout=1.0)
        except TimeoutError:
            pytest.fail("can_writer task timed out during bus init error fallback test")
        except RuntimeError as e:  # Catch the sentinel
            if "NoneType" not in str(e):
                raise

        mock_bus_cls.assert_called_once_with(channel=interface_name, bustype="failing_bustype")
        mock_logger_error.assert_any_call(
            f"CAN writer: CAN interface '{interface_name}' (failing_bustype) "
            f"is not implemented or configuration is missing: Init failed"
        )
    assert interface_name not in can_manager.buses  # Should not be added if init fails
    mock_metric_gauge.set.assert_called()  # Still called for queue management
    del os.environ["CAN_BUSTYPE"]


# --- Test for initialize_can_writer_task ---


@patch("asyncio.create_task")
@patch("core_daemon.can_manager.can_writer")  # Patch the function itself
def test_initialize_can_writer_task(mock_can_writer_function, mock_create_task):
    """
    Test that the CAN writer task is correctly initialized and scheduled.
    """
    mock_logger = MagicMock(spec=["info"])
    # Temporarily patch the logger in can_manager if it's module-level
    with patch.object(can_manager, "logger", mock_logger):
        can_manager.initialize_can_writer_task()

    mock_create_task.assert_called_once_with(mock_can_writer_function())
    mock_logger.info.assert_called_once_with("CAN writer task initialized and scheduled to run.")
