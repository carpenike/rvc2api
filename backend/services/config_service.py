"""
Config Service

Handles business logic for configuration management, including:
- Configuration retrieval and validation
- Environment variable access
- Application settings management
- Configuration updates and reloading

This service extracts configuration-related business logic from the API router layer.
"""

import logging
import os
from typing import Any

from backend.core.state import AppState

logger = logging.getLogger(__name__)


class ConfigService:
    """
    Service for managing application configuration and settings.

    This service provides business logic for configuration operations while being
    agnostic to the presentation layer (HTTP, WebSocket, etc.).
    """

    def __init__(self, app_state: AppState):
        """
        Initialize the config service.

        Args:
            app_state: Application state manager containing configuration data
        """
        self.app_state = app_state

    async def get_config_summary(self) -> dict[str, Any]:
        """
        Get a summary of the current application configuration.

        Returns:
            Dictionary containing configuration summary information
        """
        config_data = self.app_state.config_data

        summary = {
            "entities": {
                "total_configured": len(self.app_state.entity_manager.get_entity_ids()),
                "light_entities": len(self.app_state.entity_manager.get_light_entity_ids()),
                "device_types": self._get_unique_device_types(),
                "areas": self._get_unique_areas(),
            },
            "can_interfaces": {
                "configured": self._get_configured_interfaces(),
                "controller_address": self.app_state.controller_source_addr,
            },
            "system": {
                "has_coach_info": bool(getattr(self.app_state, "coach_info", None)),
                "decoder_entries": len(getattr(self.app_state, "decoder_map", {})),
                "known_command_pairs": len(self.app_state.known_command_status_pairs),
            },
            "raw_config_keys": list(config_data.keys()) if config_data else [],
        }

        return summary

    async def get_environment_info(self) -> dict[str, Any]:
        """
        Get information about relevant environment variables.

        Returns:
            Dictionary containing environment configuration
        """
        env_vars = {
            # CAN-related environment variables
            "CAN_BUSTYPE": os.getenv("CAN_BUSTYPE", "socketcan"),
            "CAN_INTERFACE": os.getenv("CAN_INTERFACE"),
            "CAN_BITRATE": os.getenv("CAN_BITRATE"),
            # Application configuration
            "CONFIG_FILE": os.getenv("CONFIG_FILE"),
            "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
            "DEBUG": os.getenv("DEBUG", "false").lower() == "true",
            # Server configuration
            "HOST": os.getenv("HOST", "127.0.0.1"),
            "PORT": os.getenv("PORT", "8000"),
            "WORKERS": os.getenv("WORKERS", "1"),
            # Feature flags
            "ENABLE_WEBSOCKETS": os.getenv("ENABLE_WEBSOCKETS", "true").lower() == "true",
            "ENABLE_CAN_SNIFFER": os.getenv("ENABLE_CAN_SNIFFER", "true").lower() == "true",
        }

        # Mask sensitive values
        masked_vars = {}
        for key, value in env_vars.items():
            if value is None:
                masked_vars[key] = None
            elif any(
                sensitive in key.lower() for sensitive in ["password", "secret", "token", "key"]
            ):
                masked_vars[key] = "***MASKED***" if value else None
            else:
                masked_vars[key] = value

        return {
            "environment_variables": masked_vars,
            "total_env_vars": len([v for v in env_vars.values() if v is not None]),
        }

    async def get_entity_configuration(self, entity_id: str | None = None) -> dict[str, Any]:
        """
        Get entity configuration details.

        Args:
            entity_id: Optional specific entity ID to retrieve

        Returns:
            Entity configuration data
        """
        if entity_id:
            entity = self.app_state.entity_manager.get_entity(entity_id)
            if not entity:
                raise ValueError(f"Entity '{entity_id}' not found in configuration")
            return {
                "entity_id": entity_id,
                "configuration": entity.config,
                "is_light": entity.config.get("device_type") == "light",
                "light_info": entity.config
                if entity.config.get("device_type") == "light"
                else None,
            }
        else:
            # Return summary of all entities
            entities = {}
            for eid, entity in self.app_state.entity_manager.get_all_entities().items():
                config = entity.config
                entities[eid] = {
                    "device_type": config.get("device_type"),
                    "suggested_area": config.get("suggested_area"),
                    "capabilities": config.get("capabilities", []),
                    "is_light": config.get("device_type") == "light",
                }
            return {"entities": entities}

    async def get_decoder_info(self) -> dict[str, Any]:
        """
        Get information about the RV-C decoder configuration.

        Returns:
            Dictionary containing decoder statistics and info
        """
        decoder_map = getattr(self.app_state, "decoder_map", {})

        # Analyze decoder entries
        pgn_count = len({entry.get("pgn") for entry in decoder_map.values() if entry.get("pgn")})
        dgn_count = len(
            {entry.get("dgn_hex") for entry in decoder_map.values() if entry.get("dgn_hex")}
        )

        return {
            "total_entries": len(decoder_map),
            "unique_pgns": pgn_count,
            "unique_dgns": dgn_count,
            "has_pgn_name_map": bool(getattr(self.app_state, "pgn_hex_to_name_map", None)),
            "sample_entries": list(decoder_map.keys())[:5],  # First 5 arbitration IDs
        }

    async def validate_configuration(self) -> dict[str, Any]:
        """
        Validate the current configuration for completeness and consistency.

        Returns:
            Dictionary containing validation results and any issues found
        """
        issues = []
        warnings = []

        # Check if basic configuration is present
        if not self.app_state.entity_manager.get_entity_ids():
            issues.append("No entities configured")

        light_entities = self.app_state.entity_manager.filter_entities(device_type="light")
        if not light_entities:
            warnings.append("No controllable lights configured")

        # Check for entities without required fields
        for entity_id, entity in self.app_state.entity_manager.get_all_entities().items():
            config = entity.config
            if not config.get("device_type"):
                warnings.append(f"Entity '{entity_id}' missing device_type")
            if not config.get("suggested_area"):
                warnings.append(f"Entity '{entity_id}' missing suggested_area")

        # Check light configurations
        for light_id, light_entity in light_entities.items():
            light_config = light_entity.config
            if not light_config.get("command_dgn"):
                issues.append(f"Light '{light_id}' missing command DGN")
            if not light_config.get("instance"):
                issues.append(f"Light '{light_id}' missing instance")

        # Check decoder configuration
        decoder_map = getattr(self.app_state, "decoder_map", {})
        if not decoder_map:
            warnings.append("No decoder map loaded - RV-C message decoding unavailable")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "summary": {
                "total_issues": len(issues),
                "total_warnings": len(warnings),
                "entities_configured": len(self.app_state.entity_manager.get_entity_ids()),
                "lights_configured": len(self.app_state.entity_manager.get_light_entity_ids()),
            },
        }

    async def get_device_mapping_content(self) -> str:
        """
        Get the content of the device mapping configuration file.

        Returns:
            String content of the device mapping file

        Raises:
            FileNotFoundError: If the device mapping file doesn't exist
            IOError: If there's an error reading the file
        """
        # Import here to avoid circular imports
        from backend.core.config_utils import get_actual_paths

        _, actual_map_path = get_actual_paths()

        if not actual_map_path or not os.path.exists(actual_map_path):
            raise FileNotFoundError(f"Device mapping file not found: {actual_map_path}")

        try:
            with open(actual_map_path, encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            raise OSError(f"Error reading device mapping file: {e}") from e

    async def get_spec_content(self) -> str:
        """
        Get the content of the RV-C specification file.

        Returns:
            String content of the spec file

        Raises:
            FileNotFoundError: If the spec file doesn't exist
            IOError: If there's an error reading the file
        """
        # Import here to avoid circular imports
        from backend.core.config_utils import get_actual_paths

        actual_spec_path, _ = get_actual_paths()

        if not actual_spec_path or not os.path.exists(actual_spec_path):
            raise FileNotFoundError(f"RV-C spec file not found: {actual_spec_path}")

        try:
            with open(actual_spec_path, encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            raise OSError(f"Error reading spec file: {e}") from e

    async def get_config_status(self) -> dict[str, Any]:
        """
        Get the status of configuration files and their loading state.

        Returns:
            Dictionary containing configuration file status information
        """
        # Import here to avoid circular imports
        from backend.core.config_utils import get_actual_paths

        actual_spec_path, actual_map_path = get_actual_paths()

        spec_loaded = actual_spec_path is not None and os.path.exists(actual_spec_path)
        mapping_loaded = actual_map_path is not None and os.path.exists(actual_map_path)

        return {
            "spec_loaded": spec_loaded,
            "spec_path": actual_spec_path if spec_loaded else None,
            "mapping_loaded": mapping_loaded,
            "mapping_path": actual_map_path if mapping_loaded else None,
        }

    def _get_unique_device_types(self) -> list[str]:
        """Get list of unique device types from entity configuration."""
        device_types = set()
        for entity in self.app_state.entity_manager.get_all_entities().values():
            device_type = entity.config.get("device_type")
            if device_type:
                device_types.add(device_type)
        return sorted(device_types)

    def _get_unique_areas(self) -> list[str]:
        """Get list of unique areas from entity configuration."""
        areas = set()
        for entity in self.app_state.entity_manager.get_all_entities().values():
            area = entity.config.get("suggested_area")
            if area:
                areas.add(area)
        return sorted(areas)

    def _get_configured_interfaces(self) -> list[str]:
        """Get list of configured CAN interfaces from light command info."""
        interfaces = set()
        light_entities = self.app_state.entity_manager.filter_entities(device_type="light")
        for light_entity in light_entities.values():
            interface = light_entity.config.get("interface")
            if interface:
                interfaces.add(interface)
        return sorted(interfaces)
