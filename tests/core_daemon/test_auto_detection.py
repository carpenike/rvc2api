"""
Unit tests for the CAN bus interface auto-detection functionality.
"""

import os
from unittest.mock import patch

import pytest

# Adjust import path to work with pytest
from core_daemon.config import get_available_can_interfaces, get_canbus_config


def test_get_available_can_interfaces_linux():
    """Test get_available_can_interfaces when running on Linux with interfaces available."""
    # We need to patch both platform and glob since our test environment may have actual interfaces
    with patch("platform.system", return_value="Linux"), patch("glob.glob", return_value=[]), patch(
        "pyroute2.IPRoute"
    ) as mock_iproute:
        # Create proper mock objects
        class MockLink:
            def get_attr(self, attr_name):
                if attr_name == "IFLA_IFNAME":
                    return self.name
                return None

        # Create two mock links with different names
        link1 = MockLink()
        link1.name = "can0"
        link2 = MockLink()
        link2.name = "can1"

        # Set up the mock IPRoute
        mock_ipr = mock_iproute.return_value.__enter__.return_value
        mock_ipr.get_links.side_effect = (
            lambda kind=None: [link1, link2] if kind in ["can", "vcan"] else []
        )

        # Call the function under test
        interfaces = get_available_can_interfaces()

        # Verify the results
        assert sorted(interfaces) == sorted(["can0", "can1"])
        assert mock_ipr.get_links.call_count >= 1


def test_get_available_can_interfaces_non_linux():
    """Test get_available_can_interfaces when not running on Linux."""
    with patch("platform.system", return_value="Darwin"):
        interfaces = get_available_can_interfaces()
        assert interfaces == []


def test_get_available_can_interfaces_fallback():
    """Test the fallback mechanism to /sys/class/net/."""
    with patch("platform.system", return_value="Linux"), patch(
        "pyroute2.IPRoute", side_effect=ImportError
    ), patch("glob.glob") as mock_glob:
        # Mock glob.glob to return specific CAN interfaces
        mock_glob.side_effect = lambda pattern: (
            ["/sys/class/net/can0", "/sys/class/net/can1"]
            if "can*" in pattern
            else ["/sys/class/net/vcan0"]
            if "vcan*" in pattern
            else []
        )

        interfaces = get_available_can_interfaces()

        # Verify the fallback detection results
        assert "can0" in interfaces
        assert "can1" in interfaces
        assert "vcan0" in interfaces
        assert mock_glob.call_count >= 2


def test_get_canbus_config_from_env():
    """Test that get_canbus_config uses values from environment variables when set."""
    with patch.dict(
        os.environ,
        {"CAN_CHANNELS": "test0,test1", "CAN_BUSTYPE": "test_bus", "CAN_BITRATE": "250000"},
        clear=True,
    ):
        config = get_canbus_config()

        assert config == {"channels": ["test0", "test1"], "bustype": "test_bus", "bitrate": 250000}


def test_get_canbus_config_auto_detection():
    """Test that get_canbus_config uses auto-detected interfaces when no environment variable is set."""
    # Remove any existing CAN_CHANNELS from environment
    with patch.dict(os.environ, {}, clear=True), patch(
        "core_daemon.config.get_available_can_interfaces", return_value=["vcan0", "vcan1"]
    ):
        config = get_canbus_config()

        assert config["channels"] == ["vcan0", "vcan1"]
        assert config["bustype"] == "socketcan"
        assert config["bitrate"] == 500000


def test_get_canbus_config_fallback():
    """Test that get_canbus_config falls back to default when no interfaces are detected or configured."""
    # Remove any existing CAN_CHANNELS from environment
    with patch.dict(os.environ, {}, clear=True), patch(
        "core_daemon.config.get_available_can_interfaces", return_value=[]
    ):
        config = get_canbus_config()

        assert config["channels"] == ["can0"]
        assert config["bustype"] == "socketcan"
        assert config["bitrate"] == 500000


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])
