#!/usr/bin/env python3
"""
Test script for the CAN bus interface auto-detection functionality.

This script tests the CAN bus interface auto-detection functionality in
the rvc2api project. It runs through different test scenarios to verify
that the auto-detection works correctly.

Usage:
    python test_canbus_config.py

This will:
1. Test auto-detection without any environment variables set
2. Test with CAN_CHANNELS=can0 environment variable
3. Test with CAN_CHANNELS=can0,can1 environment variable
4. Test auto-detection logic on non-Linux systems
5. Restore the original environment when finished
"""

import os
import platform
import sys

# Import the functions from the module directly
from backend.core.config import get_available_can_interfaces, get_canbus_config

# Add the parent directory to the Python path to allow imports from src
sys.path.insert(0, os.path.abspath("."))


def format_config(config):
    """Format the config dictionary for clearer output."""
    return {
        "channels": config.get("channels"),
        "bustype": config.get("bustype"),
        "bitrate": config.get("bitrate"),
    }


def main():
    """
    Test the get_canbus_config function with different environment configurations.
    """
    print("=== CAN Bus Interface Auto-Detection Test ===")
    print(f"System: {platform.system()} {platform.release()}")

    # Save original environment variables if they exist
    orig_channels = os.environ.get("CAN_CHANNELS")
    orig_bustype = os.environ.get("CAN_BUSTYPE")
    orig_bitrate = os.environ.get("CAN_BITRATE")

    # Remove environment variables for clean testing
    if "CAN_CHANNELS" in os.environ:
        del os.environ["CAN_CHANNELS"]

    # Test 1: Auto-detection without environment variables
    print("\nTest 1: Without CAN_CHANNELS environment variable (auto-detection)")
    available = get_available_can_interfaces()
    print(f"Available interfaces: {available}")
    config1 = get_canbus_config()
    print(f"Canbus config: {format_config(config1)}")

    # Test 2: Single interface specified in environment variable
    print("\nTest 2: With CAN_CHANNELS=can0 environment variable")
    os.environ["CAN_CHANNELS"] = "can0"
    config2 = get_canbus_config()
    print(f"Canbus config: {format_config(config2)}")

    # Test 3: Multiple interfaces specified in environment variable
    print("\nTest 3: With CAN_CHANNELS=can0,can1 environment variable")
    os.environ["CAN_CHANNELS"] = "can0,can1"
    config3 = get_canbus_config()
    print(f"Canbus config: {format_config(config3)}")

    # Test 4: Custom bustype and bitrate
    print("\nTest 4: With custom bustype and bitrate")
    os.environ["CAN_CHANNELS"] = "can0"
    os.environ["CAN_BUSTYPE"] = "custom_bustype"
    os.environ["CAN_BITRATE"] = "125000"
    config4 = get_canbus_config()
    print(f"Canbus config: {format_config(config4)}")

    # Restore original environment variables if they existed
    if orig_channels is not None:
        os.environ["CAN_CHANNELS"] = orig_channels
    elif "CAN_CHANNELS" in os.environ:
        del os.environ["CAN_CHANNELS"]

    if orig_bustype is not None:
        os.environ["CAN_BUSTYPE"] = orig_bustype
    elif "CAN_BUSTYPE" in os.environ:
        del os.environ["CAN_BUSTYPE"]

    if orig_bitrate is not None:
        os.environ["CAN_BITRATE"] = orig_bitrate
    elif "CAN_BITRATE" in os.environ:
        del os.environ["CAN_BITRATE"]

    print("\nEnvironment variables restored to original state.")


if __name__ == "__main__":
    main()
