#!/usr/bin/env python
"""
Simple test script to send and receive CAN messages using virtual CAN interfaces.
"""

import argparse
import logging
import time

import can


def configure_logging():
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    return logging.getLogger("can_test")


def send_test_messages(interface="vcan0", count=10, interval=1.0):
    """Send a series of test messages to the specified CAN interface."""
    logger = configure_logging()

    try:
        logger.info(f"Setting up CAN bus on {interface}")
        bus = can.interface.Bus(channel=interface, bustype="socketcan")

        for i in range(count):
            # Create a test message
            message = can.Message(
                arbitration_id=0x123,  # Standard ID
                data=[i, 0x55, 0xAA, 0xFF, 0, 0, 0, 0],
                is_extended_id=False,
            )

            try:
                bus.send(message)
                logger.info(f"Message {i+1}/{count} sent: {message}")
            except can.CanError as e:
                logger.error(f"Message NOT sent: {e}")

            time.sleep(interval)

        logger.info("All messages sent, closing bus")
        bus.shutdown()

    except Exception as e:
        logger.error(f"Error during CAN communication: {e}")


def monitor_can_bus(interface="vcan0", duration=30):
    """Monitor and log all messages on the specified CAN interface for a given duration."""
    logger = configure_logging()

    try:
        logger.info(f"Setting up CAN bus monitoring on {interface}")
        bus = can.interface.Bus(channel=interface, bustype="socketcan")

        logger.info(f"Monitoring CAN messages for {duration} seconds. Press Ctrl+C to exit.")
        timeout = time.time() + duration

        while time.time() < timeout:
            message = bus.recv(1)  # 1 second timeout
            if message:
                logger.info(f"Received message: {message}")

        logger.info("Monitoring complete, closing bus")
        bus.shutdown()

    except KeyboardInterrupt:
        logger.info("Monitoring stopped by user")
        if "bus" in locals():
            bus.shutdown()
    except Exception as e:
        logger.error(f"Error during CAN monitoring: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test vCAN interfaces")
    parser.add_argument(
        "--action",
        choices=["send", "monitor"],
        required=True,
        help="Action to perform: send test messages or monitor the bus",
    )
    parser.add_argument(
        "--interface", default="vcan0", help="CAN interface to use (default: vcan0)"
    )
    parser.add_argument(
        "--count", type=int, default=10, help="Number of messages to send (default: 10)"
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Interval between messages in seconds (default: 1.0)",
    )
    parser.add_argument(
        "--duration", type=int, default=30, help="Duration to monitor bus in seconds (default: 30)"
    )

    args = parser.parse_args()

    if args.action == "send":
        send_test_messages(args.interface, args.count, args.interval)
    else:
        monitor_can_bus(args.interface, args.duration)
