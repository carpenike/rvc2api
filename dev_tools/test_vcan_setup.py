#!/usr/bin/env python3
"""Test vCAN functionality with Python can library.

This script verifies that vCAN interfaces are properly set up and can be used
with the python-can library. It sends a test message on vcan0 and listens for
messages on the same interface.

Usage:
    python test_vcan_setup.py
"""

import sys
import time
from threading import Thread

try:
    import can
except ImportError:
    print("Error: python-can package not installed.")
    print("Please install it with: pip install python-can")
    sys.exit(1)


def listener_thread():
    """Set up a CAN bus listener and print received messages."""
    try:
        bus = can.interface.Bus(channel="vcan0", interface="socketcan")
        print("Listening for messages on vcan0...")

        # Set up a simple listener
        for msg in bus:
            print(f"Received message: {msg}")
            if msg.arbitration_id == 0x123:
                print(
                    f"✓ Test message verified: ID=0x{msg.arbitration_id:x}, data={msg.data.hex()}"
                )
                break

    except can.CanError as e:
        print(f"Error setting up CAN listener: {e}")
        return False
    finally:
        if "bus" in locals():
            bus.shutdown()

    return True


def main():
    """Test vCAN functionality by sending and receiving a message."""
    # Check if vcan0 is available
    try:
        # Start listener thread
        listener = Thread(target=listener_thread)
        listener.daemon = True
        listener.start()

        # Give the listener time to start
        time.sleep(0.5)

        # Send a test message
        with can.interface.Bus(channel="vcan0", interface="socketcan") as bus:
            print("Sending test message on vcan0...")
            message = can.Message(
                arbitration_id=0x123,
                data=[0xDE, 0xAD, 0xBE, 0xEF],
                is_extended_id=False,
            )
            bus.send(message)
            print(f"Sent message: ID=0x{message.arbitration_id:x}, data={message.data.hex()}")

        # Wait for confirmation
        listener.join(timeout=2.0)
        if listener.is_alive():
            print("❌ Test message was not received within timeout period.")
            return False

        return True

    except can.CanError as e:
        print(f"Error setting up CAN bus: {e}")
        print("Please ensure that the vcan0 interface is available and up.")
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("vCAN Setup Verification")
    print("=" * 50)

    success = main()

    if success:
        print("\n✅ vCAN setup verified successfully!")
        sys.exit(0)
    else:
        print("\n❌ vCAN setup verification failed.")
        sys.exit(1)
