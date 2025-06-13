"""
J1939 to RV-C protocol bridge implementation.

This module provides bidirectional translation between J1939 and RV-C protocols,
enabling unified entity management and control across both protocol domains.

Key features:
- Engine data translation (J1939 engine PGNs → RV-C engine status)
- Transmission data translation (J1939 transmission PGNs → RV-C transmission status)
- Chassis data bridging for unified vehicle status
- Command translation for cross-protocol control
- Entity mapping and state synchronization
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

from backend.core.config import Settings
from backend.integrations.j1939.decoder import J1939Message, SystemType

logger = logging.getLogger(__name__)


class BridgeDirection(Enum):
    """Direction of protocol bridging."""

    J1939_TO_RVC = "j1939_to_rvc"
    RVC_TO_J1939 = "rvc_to_j1939"
    BIDIRECTIONAL = "bidirectional"


@dataclass
class EntityMapping:
    """Mapping between J1939 data and RV-C entities."""

    j1939_pgn: int
    rvc_dgn_hex: str
    entity_id: str
    system_type: SystemType
    signal_mappings: dict[str, str]  # J1939 signal → RV-C signal
    scaling_factors: dict[str, float] = None  # Optional scaling adjustments
    active: bool = True


@dataclass
class BridgedData:
    """Container for bridged protocol data."""

    source_protocol: str
    target_protocol: str
    entity_id: str
    original_data: dict[str, Any]
    translated_data: dict[str, Any]
    timestamp: float


class J1939ProtocolBridge:
    """
    Protocol bridge for translating between J1939 and RV-C protocols.

    This bridge enables unified entity management by translating J1939 engine,
    transmission, and chassis data into RV-C format, and vice versa for commands.
    """

    def __init__(self, settings: Settings):
        """
        Initialize the J1939 protocol bridge.

        Args:
            settings: Application settings containing bridge configuration
        """
        self.settings = settings
        self.j1939_config = settings.j1939
        self._entity_mappings: dict[int, EntityMapping] = {}
        self._reverse_mappings: dict[str, EntityMapping] = {}  # RV-C → J1939
        self._active = False
        self._bridge_stats = {
            "messages_bridged": 0,
            "translation_errors": 0,
            "entity_updates": 0,
            "commands_translated": 0,
        }

        # Initialize entity mappings
        self._initialize_entity_mappings()

    async def startup(self) -> None:
        """Start the protocol bridge."""
        if not self.j1939_config.enable_rvc_bridge:
            logger.info("J1939 to RV-C bridge is disabled")
            return

        self._active = True
        logger.info("J1939 Protocol Bridge started")

    async def shutdown(self) -> None:
        """Stop the protocol bridge."""
        self._active = False
        logger.info("J1939 Protocol Bridge stopped")

    def bridge_j1939_to_rvc(self, j1939_message: J1939Message) -> BridgedData | None:
        """
        Translate a J1939 message to RV-C format.

        Args:
            j1939_message: Decoded J1939 message

        Returns:
            BridgedData containing translated information, or None if no mapping exists
        """
        if not self._active:
            return None

        mapping = self._entity_mappings.get(j1939_message.pgn)
        if not mapping or not mapping.active:
            return None

        try:
            # Translate J1939 signals to RV-C format
            translated_signals = self._translate_signals_j1939_to_rvc(
                j1939_message.decoded_signals, mapping
            )

            # Create RV-C compatible data structure
            rvc_data = {
                "dgn_hex": mapping.rvc_dgn_hex,
                "entity_id": mapping.entity_id,
                "instance": 0,  # Default instance
                "signals": translated_signals,
                "source_address": j1939_message.source_address,
                "system_type": mapping.system_type.value,
                "timestamp": j1939_message.timestamp,
            }

            bridged_data = BridgedData(
                source_protocol="j1939",
                target_protocol="rvc",
                entity_id=mapping.entity_id,
                original_data=j1939_message.decoded_signals,
                translated_data=rvc_data,
                timestamp=j1939_message.timestamp or 0.0,
            )

            self._bridge_stats["messages_bridged"] += 1
            self._bridge_stats["entity_updates"] += 1

            return bridged_data

        except Exception as e:
            logger.error(f"Error bridging J1939 PGN {j1939_message.pgn:04X} to RV-C: {e}")
            self._bridge_stats["translation_errors"] += 1
            return None

    def bridge_rvc_to_j1939(
        self, rvc_entity_id: str, rvc_command: dict[str, Any]
    ) -> dict[str, Any] | None:
        """
        Translate an RV-C command to J1939 format.

        Args:
            rvc_entity_id: RV-C entity identifier
            rvc_command: RV-C command data

        Returns:
            Dictionary containing J1939 command data, or None if no mapping exists
        """
        if not self._active:
            return None

        mapping = self._reverse_mappings.get(rvc_entity_id)
        if not mapping or not mapping.active:
            return None

        try:
            # Translate RV-C command to J1939 format
            j1939_data = self._translate_command_rvc_to_j1939(rvc_command, mapping)

            self._bridge_stats["commands_translated"] += 1

            return j1939_data

        except Exception as e:
            logger.error(f"Error bridging RV-C command for {rvc_entity_id} to J1939: {e}")
            self._bridge_stats["translation_errors"] += 1
            return None

    def get_bridge_status(self) -> dict[str, Any]:
        """
        Get current bridge status and statistics.

        Returns:
            Dictionary containing bridge status information
        """
        return {
            "active": self._active,
            "enabled": self.j1939_config.enable_rvc_bridge,
            "entity_mappings": len(self._entity_mappings),
            "statistics": self._bridge_stats.copy(),
            "supported_systems": list(
                {mapping.system_type.value for mapping in self._entity_mappings.values()}
            ),
        }

    def get_entity_mappings(self) -> dict[str, dict[str, Any]]:
        """
        Get all entity mappings for diagnostic purposes.

        Returns:
            Dictionary of entity mappings with their configurations
        """
        return {
            mapping.entity_id: {
                "j1939_pgn": mapping.j1939_pgn,
                "rvc_dgn_hex": mapping.rvc_dgn_hex,
                "system_type": mapping.system_type.value,
                "signal_mappings": mapping.signal_mappings,
                "active": mapping.active,
            }
            for mapping in self._entity_mappings.values()
        }

    def _initialize_entity_mappings(self) -> None:
        """Initialize entity mappings between J1939 and RV-C protocols."""

        # Engine RPM and Status Mapping
        if self.j1939_config.bridge_engine_data:
            engine_mapping = EntityMapping(
                j1939_pgn=61444,  # Electronic Engine Controller 1
                rvc_dgn_hex="1FFFF",  # Engine Operating Parameters
                entity_id="engine_primary",
                system_type=SystemType.ENGINE,
                signal_mappings={
                    "engine_speed": "engine_speed",
                    "actual_engine_torque_percent": "engine_load",
                    "engine_demand_torque_percent": "engine_demand",
                },
                scaling_factors={
                    "engine_speed": 1.0,  # RPM to RPM
                    "actual_engine_torque_percent": 1.0,  # % to %
                },
            )
            self._entity_mappings[61444] = engine_mapping
            self._reverse_mappings["engine_primary"] = engine_mapping

            # Engine Temperature Mapping
            engine_temp_mapping = EntityMapping(
                j1939_pgn=65262,  # Engine Temperature 1
                rvc_dgn_hex="1FEFF",  # Engine Temperature Parameters
                entity_id="engine_temperature",
                system_type=SystemType.ENGINE,
                signal_mappings={
                    "engine_coolant_temp": "coolant_temperature",
                    "fuel_temp": "fuel_temperature",
                    "engine_oil_temp": "oil_temperature",
                },
                scaling_factors={
                    "engine_coolant_temp": 1.0,  # °C to °C
                    "fuel_temp": 1.0,  # °C to °C
                    "engine_oil_temp": 1.0,  # °C to °C
                },
            )
            self._entity_mappings[65262] = engine_temp_mapping
            self._reverse_mappings["engine_temperature"] = engine_temp_mapping

        # Transmission Status Mapping
        if self.j1939_config.bridge_transmission_data:
            transmission_mapping = EntityMapping(
                j1939_pgn=61443,  # Electronic Transmission Controller 1
                rvc_dgn_hex="1FEFF",  # Transmission Operating Parameters
                entity_id="transmission_primary",
                system_type=SystemType.TRANSMISSION,
                signal_mappings={
                    "transmission_current_gear": "current_gear",
                    "transmission_selected_gear": "selected_gear",
                    "transmission_actual_gear_ratio": "gear_ratio",
                },
                scaling_factors={
                    "transmission_current_gear": 1.0,
                    "transmission_selected_gear": 1.0,
                    "transmission_actual_gear_ratio": 1.0,
                },
            )
            self._entity_mappings[61443] = transmission_mapping
            self._reverse_mappings["transmission_primary"] = transmission_mapping

            # Transmission Temperature and Pressure
            trans_temp_mapping = EntityMapping(
                j1939_pgn=65272,  # Electronic Transmission Controller 2
                rvc_dgn_hex="1FEFE",  # Transmission Temperature Parameters
                entity_id="transmission_temperature",
                system_type=SystemType.TRANSMISSION,
                signal_mappings={
                    "transmission_fluid_temp": "fluid_temperature",
                    "transmission_oil_pressure": "oil_pressure",
                    "transmission_output_shaft_speed": "output_shaft_speed",
                    "transmission_input_shaft_speed": "input_shaft_speed",
                },
            )
            self._entity_mappings[65272] = trans_temp_mapping
            self._reverse_mappings["transmission_temperature"] = trans_temp_mapping

        # Vehicle Speed and Chassis
        chassis_mapping = EntityMapping(
            j1939_pgn=65265,  # Cruise Control/Vehicle Speed
            rvc_dgn_hex="1FEF1",  # Vehicle Speed and Control
            entity_id="vehicle_speed",
            system_type=SystemType.CHASSIS,
            signal_mappings={
                "wheel_based_vehicle_speed": "vehicle_speed",
                "cruise_control_active": "cruise_active",
                "cruise_control_set_speed": "cruise_set_speed",
                "brake_switch": "brake_status",
            },
            scaling_factors={
                "wheel_based_vehicle_speed": 1.0,  # km/h to km/h
            },
        )
        self._entity_mappings[65265] = chassis_mapping
        self._reverse_mappings["vehicle_speed"] = chassis_mapping

        logger.info(f"Initialized {len(self._entity_mappings)} J1939-RV-C entity mappings")

    def _translate_signals_j1939_to_rvc(
        self, j1939_signals: dict[str, Any], mapping: EntityMapping
    ) -> dict[str, Any]:
        """
        Translate J1939 signals to RV-C format using entity mapping.

        Args:
            j1939_signals: Original J1939 signal values
            mapping: Entity mapping configuration

        Returns:
            Dictionary of translated RV-C signals
        """
        translated = {}

        for j1939_signal, rvc_signal in mapping.signal_mappings.items():
            if j1939_signal in j1939_signals:
                value = j1939_signals[j1939_signal]

                # Apply scaling factor if specified
                if mapping.scaling_factors and j1939_signal in mapping.scaling_factors:
                    value = value * mapping.scaling_factors[j1939_signal]

                # Convert to RV-C signal format
                translated[rvc_signal] = self._convert_to_rvc_format(value, rvc_signal)

        return translated

    def _translate_command_rvc_to_j1939(
        self, rvc_command: dict[str, Any], mapping: EntityMapping
    ) -> dict[str, Any]:
        """
        Translate RV-C command to J1939 format.

        Args:
            rvc_command: RV-C command data
            mapping: Entity mapping configuration

        Returns:
            Dictionary containing J1939 command data
        """
        j1939_data = {
            "pgn": mapping.j1939_pgn,
            "signals": {},
        }

        # Reverse signal mapping (RV-C → J1939)
        reverse_signal_mapping = {v: k for k, v in mapping.signal_mappings.items()}

        for rvc_signal, value in rvc_command.items():
            if rvc_signal in reverse_signal_mapping:
                j1939_signal = reverse_signal_mapping[rvc_signal]

                # Apply reverse scaling if specified
                if mapping.scaling_factors and j1939_signal in mapping.scaling_factors:
                    scaling_factor = mapping.scaling_factors[j1939_signal]
                    if scaling_factor != 0:
                        value = value / scaling_factor

                j1939_data["signals"][j1939_signal] = value

        return j1939_data

    def _convert_to_rvc_format(self, value: Any, signal_name: str) -> Any:
        """
        Convert a value to RV-C compatible format.

        Args:
            value: Value to convert
            signal_name: Name of the RV-C signal

        Returns:
            Converted value in RV-C format
        """
        # Handle special RV-C signal conversions
        if "temperature" in signal_name.lower():
            # Ensure temperature is in Celsius
            return float(value)
        if "speed" in signal_name.lower():
            # Ensure speed values are properly formatted
            return float(value)
        if "pressure" in signal_name.lower():
            # Ensure pressure values are in proper units
            return float(value)
        if "status" in signal_name.lower() or "active" in signal_name.lower():
            # Convert to boolean for status signals
            return bool(value)
        # Default conversion
        return value
