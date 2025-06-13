"""
CAN Interface Service

Service for managing CAN interface mappings and resolution.
Provides logical interface name mapping to physical interfaces.
"""

import logging
from typing import Any

from backend.core.config import get_settings

logger = logging.getLogger(__name__)


class CANInterfaceService:
    """Service for managing CAN interface mappings and resolution."""

    def __init__(self):
        self.settings = get_settings()
        self._interface_mappings = self._load_interface_mappings()

    def _load_interface_mappings(self) -> dict[str, str]:
        """Load interface mappings from settings."""
        return self.settings.can.interface_mappings.copy()

    def resolve_interface(self, logical_name: str) -> str:
        """
        Resolve logical interface name to physical interface.

        Args:
            logical_name: Logical interface name (e.g., 'house', 'chassis')

        Returns:
            Physical interface name (e.g., 'can0', 'can1')

        Raises:
            ValueError: If logical interface is not mapped
        """
        # If it's already physical, return as-is
        if logical_name.startswith(("can", "vcan")):
            return logical_name

        if logical_name in self._interface_mappings:
            return self._interface_mappings[logical_name]

        msg = f"Unknown logical CAN interface: {logical_name}"
        raise ValueError(msg)

    def get_all_mappings(self) -> dict[str, str]:
        """Get all current interface mappings."""
        return self._interface_mappings.copy()

    def update_mapping(self, logical_name: str, physical_interface: str) -> None:
        """Update interface mapping (runtime only)."""
        self._interface_mappings[logical_name] = physical_interface
        logger.info(f"Updated interface mapping: {logical_name} -> {physical_interface}")

    def validate_mapping(self, mappings: dict[str, str]) -> dict[str, Any]:
        """Validate interface mappings."""
        issues = []

        # Check for duplicate physical interfaces
        physical_interfaces = list(mappings.values())
        if len(physical_interfaces) != len(set(physical_interfaces)):
            issues.append("Duplicate physical interfaces detected")

        # Validate physical interface names
        for physical in mappings.values():
            if not physical.startswith(("can", "vcan")):
                issues.append(f"Invalid physical interface: {physical}")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "mapping": mappings,
        }
