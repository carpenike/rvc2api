"""
Coach Mapping Service

Service for managing coach mapping configurations with interface resolution.
Integrates logical CAN interfaces with coach mapping definitions.
"""

import logging
from typing import Any

import yaml

from backend.core.config import get_rvc_settings

logger = logging.getLogger(__name__)


class CoachMappingService:
    """Service for managing coach mapping configurations."""

    def __init__(self, can_interface_service):
        self.rvc_settings = get_rvc_settings()
        self.can_interface_service = can_interface_service
        self._mapping_cache = None

    def get_current_mapping(self) -> dict[str, Any]:
        """Get current coach mapping with resolved interfaces."""
        if self._mapping_cache is None:
            self._load_mapping()
        return self._mapping_cache or {}

    def _load_mapping(self):
        """Load coach mapping from file with interface resolution."""
        mapping_path = self.rvc_settings.get_coach_mapping_path()

        with open(mapping_path) as f:
            raw_mapping = yaml.safe_load(f)

        # Resolve logical interfaces to physical interfaces
        self._mapping_cache = self._resolve_interfaces(raw_mapping)

    def _resolve_interfaces(self, mapping: dict[str, Any]) -> dict[str, Any]:
        """Resolve logical interfaces to physical interfaces throughout mapping."""

        def resolve_recursive(obj):
            if isinstance(obj, dict):
                if "interface" in obj:
                    logical_interface = obj["interface"]
                    try:
                        obj["interface"] = self.can_interface_service.resolve_interface(
                            logical_interface
                        )
                        obj["_logical_interface"] = logical_interface  # Keep for reference
                    except ValueError:
                        # Keep original if can't resolve
                        pass

                for value in obj.values():
                    resolve_recursive(value)

            elif isinstance(obj, list):
                for item in obj:
                    resolve_recursive(item)

        resolved = mapping.copy()
        resolve_recursive(resolved)
        return resolved

    def reload_mapping(self):
        """Reload coach mapping from file."""
        self._mapping_cache = None
        self._load_mapping()

    def get_interface_requirements(self) -> dict[str, Any]:
        """Get interface requirements from coach config (informational only)."""
        mapping = self.get_current_mapping()
        return mapping.get("interface_requirements", {})

    def get_runtime_interface_mappings(self) -> dict[str, str]:
        """Get actual runtime interface mappings from CAN service."""
        return self.can_interface_service.get_all_mappings()

    def validate_interface_compatibility(self) -> dict[str, Any]:
        """Validate that runtime mappings are compatible with coach requirements."""
        requirements = self.get_interface_requirements()
        runtime_mappings = self.get_runtime_interface_mappings()

        issues = []
        recommendations = []

        # Check if all required logical interfaces are mapped
        for logical_name, req_info in requirements.items():
            if logical_name not in runtime_mappings:
                issues.append(
                    f"Required logical interface '{logical_name}' not mapped to physical interface"
                )
            else:
                # Check for speed recommendations (informational)
                recommended_speed = req_info.get("recommended_speed")
                if recommended_speed:
                    recommendations.append(
                        f"Interface '{logical_name}' -> '{runtime_mappings[logical_name]}': "
                        f"recommended speed {recommended_speed} bps"
                    )

        # Check for unmapped runtime interfaces
        for logical_name in runtime_mappings:
            if logical_name not in requirements:
                recommendations.append(
                    f"Runtime interface '{logical_name}' has no coach requirements defined"
                )

        return {
            "compatible": len(issues) == 0,
            "issues": issues,
            "recommendations": recommendations,
            "requirements": requirements,
            "runtime_mappings": runtime_mappings,
        }

    def get_mapping_metadata(self) -> dict[str, Any]:
        """Get metadata about current coach mapping."""
        mapping = self.get_current_mapping()

        # Extract metadata
        coach_info = mapping.get("coach_info", {})
        file_metadata = mapping.get("file_metadata", {})
        interface_requirements = mapping.get("interface_requirements", {})

        # Count devices and interfaces
        device_count = 0
        logical_interfaces_used = set()
        physical_interfaces_used = set()

        for dgn_hex, instances in mapping.items():
            if dgn_hex.startswith(
                (
                    "1",
                    "2",
                    "3",
                    "4",
                    "5",
                    "6",
                    "7",
                    "8",
                    "9",
                    "A",
                    "B",
                    "C",
                    "D",
                    "E",
                    "F",
                )
            ):
                for devices in instances.values():
                    if isinstance(devices, list):
                        device_count += len(devices)
                        for device in devices:
                            if isinstance(device, dict) and "interface" in device:
                                # Track both resolved physical and original logical interfaces
                                physical_interfaces_used.add(device["interface"])
                                if "_logical_interface" in device:
                                    logical_interfaces_used.add(device["_logical_interface"])

        return {
            "coach_info": coach_info,
            "file_metadata": file_metadata,
            "device_count": device_count,
            "logical_interfaces_used": list(logical_interfaces_used),
            "physical_interfaces_used": list(physical_interfaces_used),
            "interface_requirements": interface_requirements,
            "interface_compatibility": self.validate_interface_compatibility(),
            "mapping_path": str(self.rvc_settings.get_coach_mapping_path()),
        }
