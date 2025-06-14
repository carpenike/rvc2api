"""
Spartan K2 Chassis Feature Integration

This module provides feature management integration for Spartan K2 chassis systems,
following the established patterns from RV-C, J1939, and Firefly implementations.

Key capabilities:
- Feature lifecycle management (startup, shutdown, health monitoring)
- Configuration integration with Pydantic settings
- Real-time chassis system monitoring and diagnostics
- Safety interlock management and validation
- Seamless integration with existing CAN and entity management systems

Architecture:
- Follows proven Feature base class patterns
- Integrates with existing dependency injection system
- Provides comprehensive health monitoring and status reporting
- Supports graceful degradation when optional components fail
"""

import logging
from typing import Any

from backend.integrations.j1939.spartan_k2_extensions import SpartanK2Decoder, SpartanK2SystemType
from backend.services.feature_base import Feature
from backend.services.feature_models import SafetyClassification

logger = logging.getLogger(__name__)


class SpartanK2Feature(Feature):
    """
    Spartan K2 chassis feature providing comprehensive chassis system integration.

    This feature enables advanced Spartan K2 chassis capabilities including:
    - Real-time brake, suspension, and steering system monitoring
    - Safety interlock validation and enforcement
    - Advanced diagnostic capabilities with DTC extraction
    - Integration with existing J1939 and RV-C entity management
    - Chassis-to-coach communication bridging
    """

    def __init__(
        self,
        name: str = "spartan_k2",
        enabled: bool = False,
        core: bool = False,
        config: dict[str, Any] | None = None,
        dependencies: list[str] | None = None,
        friendly_name: str | None = None,
        safety_classification: SafetyClassification | None = None,
        log_state_transitions: bool = True,
    ):
        """
        Initialize the Spartan K2 feature.

        Args:
            name: The name of the feature (default: "spartan_k2")
            enabled: Whether the feature is enabled (default: False)
            core: Whether this is a core feature (default: False)
            config: Configuration options for the feature
            dependencies: List of feature names this feature depends on
            friendly_name: Human-readable display name for the feature
            safety_classification: Safety classification for state validation
            log_state_transitions: Whether to log state transitions for audit
        """
        super().__init__(
            name=name,
            enabled=enabled,
            core=core,
            config=config or {},
            dependencies=dependencies or ["j1939"],
            friendly_name=friendly_name or "Spartan K2 Chassis",
            safety_classification=safety_classification,
            log_state_transitions=log_state_transitions,
        )

        # Initialize internal state
        self._decoder: SpartanK2Decoder | None = None
        self._message_count = 0
        self._error_count = 0
        self._last_message_time: float | None = None
        self._system_health: dict[str, Any] = {}

    # Properties are handled by base class, but we can add configuration handling
    def _get_config_value(self, key: str, default: Any = None) -> Any:
        """Get configuration value from self.config."""
        return self.config.get(key, default)

    @property
    def health(self) -> str:
        """Returns the health status of the Spartan K2 feature."""
        if not self._decoder:
            return "not_initialized"

        if not self.is_healthy():
            return "unhealthy"

        return "healthy"

    async def startup(self) -> None:
        """
        Initialize Spartan K2 chassis integration.

        Sets up the decoder, validates configuration, and prepares
        for real-time chassis system monitoring.
        """
        try:
            # Create a mock settings object from configuration
            from backend.core.config import get_settings

            settings = get_settings()

            # Initialize the Spartan K2 decoder
            self._decoder = SpartanK2Decoder(settings)

            # Initialize system health tracking
            self._initialize_system_health()

            # Log startup configuration
            decoder_info = self._decoder.get_decoder_info()
            logger.info(
                f"Spartan K2 feature started: {decoder_info['pgn_definitions']} PGNs, "
                f"safety interlocks: {decoder_info['configuration']['safety_interlocks']}, "
                f"diagnostics: {decoder_info['configuration']['advanced_diagnostics']}"
            )

        except Exception as e:
            logger.error(f"Failed to start Spartan K2 feature: {e}")
            raise

    async def shutdown(self) -> None:
        """
        Gracefully shutdown Spartan K2 integration.

        Cleans up resources and logs final statistics.
        """
        if self._decoder:
            logger.info(
                f"Spartan K2 feature shutdown: {self._message_count} messages processed, "
                f"{self._error_count} errors"
            )

        self._decoder = None
        self._system_health.clear()

    def is_healthy(self) -> bool:
        """
        Check overall health of the Spartan K2 feature.

        Returns:
            True if all critical systems are operational
        """
        if not self._decoder:
            return False

        # Check for critical system failures
        for system_type in [SpartanK2SystemType.BRAKES, SpartanK2SystemType.STEERING]:
            system_status = self._decoder.get_system_status(system_type)
            if system_status.get("safety_status") == "violation":
                return False

        # Check error rate
        if self._message_count > 100:
            error_rate = self._error_count / self._message_count
            if error_rate > 0.1:  # More than 10% error rate
                return False

        return True

    def get_status(self) -> dict[str, Any]:
        """
        Get comprehensive status of the Spartan K2 feature.

        Returns:
            Dictionary containing detailed status information
        """
        if not self._decoder:
            return {"enabled": False, "status": "not_initialized", "error": "Decoder not available"}

        # Get decoder information
        decoder_info = self._decoder.get_decoder_info()

        # Get system-specific status
        systems_status = {}
        for system_type in SpartanK2SystemType:
            systems_status[system_type.value] = self._decoder.get_system_status(system_type)

        return {
            "enabled": True,
            "status": "operational",
            "decoder_info": decoder_info,
            "systems": systems_status,
            "statistics": {
                "messages_processed": self._message_count,
                "errors": self._error_count,
                "error_rate": self._error_count / max(self._message_count, 1),
                "last_message_time": self._last_message_time,
            },
            "health": self._system_health,
            "configuration": {
                "safety_interlocks_enabled": self._get_config_value(
                    "enable_safety_interlocks", True
                ),
                "advanced_diagnostics_enabled": self._get_config_value(
                    "enable_advanced_diagnostics", True
                ),
                "chassis_interface": self._get_config_value("chassis_interface", "chassis"),
            },
        }

    def decode_message(
        self,
        pgn: int,
        source_address: int,
        data: bytes,
        priority: int = 6,
        timestamp: float | None = None,
    ) -> dict[str, Any] | None:
        """
        Decode a Spartan K2 chassis message.

        Args:
            pgn: Parameter Group Number
            source_address: Source address of the message
            data: Message data bytes
            priority: Message priority (0-7, lower is higher priority)
            timestamp: Optional timestamp

        Returns:
            Decoded message data or None if not a Spartan K2 message
        """
        if not self._decoder:
            return None

        try:
            # Attempt to decode the message
            message = self._decoder.decode_message(pgn, source_address, data, priority, timestamp)

            if message:
                self._message_count += 1
                self._last_message_time = timestamp

                # Update system health tracking
                self._update_system_health(message)

                # Convert to dictionary for API response
                return {
                    "pgn": message.pgn,
                    "source_address": message.source_address,
                    "system_type": message.system_type.value,
                    "decoded_signals": message.decoded_signals,
                    "safety_interlocks": message.safety_interlocks,
                    "diagnostic_codes": message.diagnostic_codes,
                    "timestamp": message.timestamp,
                    "manufacturer": "Spartan",
                    "chassis_model": "K2",
                }

            return None

        except Exception as e:
            self._error_count += 1
            logger.error(f"Error decoding Spartan K2 message PGN 0x{pgn:04X}: {e}")
            return None

    def get_system_diagnostics(self, system_type: str) -> dict[str, Any]:
        """
        Get detailed diagnostics for a specific chassis system.

        Args:
            system_type: Type of system to get diagnostics for

        Returns:
            Comprehensive diagnostic information
        """
        if not self._decoder:
            return {"error": "Decoder not available"}

        try:
            # Convert string to enum
            system_enum = SpartanK2SystemType(system_type)
            return self._decoder.get_system_status(system_enum)
        except ValueError:
            return {"error": f"Unknown system type: {system_type}"}
        except Exception as e:
            logger.error(f"Error getting Spartan K2 system diagnostics: {e}")
            return {"error": str(e)}

    def validate_safety_interlocks(self) -> dict[str, Any]:
        """
        Perform comprehensive safety interlock validation across all systems.

        Returns:
            Safety validation results and recommendations
        """
        if not self._decoder:
            return {"error": "Decoder not available"}

        safety_status = {
            "overall_status": "unknown",
            "critical_violations": [],
            "warnings": [],
            "systems_checked": [],
            "recommendations": [],
        }

        try:
            # Check each critical system
            critical_systems = [
                SpartanK2SystemType.BRAKES,
                SpartanK2SystemType.STEERING,
                SpartanK2SystemType.SUSPENSION,
            ]

            has_critical_violations = False

            for system_type in critical_systems:
                system_status = self._decoder.get_system_status(system_type)
                safety_status["systems_checked"].append(system_type.value)

                if system_status.get("safety_status") == "violation":
                    has_critical_violations = True
                    safety_status["critical_violations"].extend(
                        system_status.get("interlock_violations", [])
                    )

                # Add diagnostic codes as warnings
                diagnostic_codes = system_status.get("diagnostic_codes", [])
                if diagnostic_codes:
                    safety_status["warnings"].append(
                        f"{system_type.value} has diagnostic codes: {diagnostic_codes}"
                    )

            # Determine overall status
            if has_critical_violations:
                safety_status["overall_status"] = "critical"
                safety_status["recommendations"].append(
                    "Immediate attention required - critical safety violations detected"
                )
            elif safety_status["warnings"]:
                safety_status["overall_status"] = "warning"
                safety_status["recommendations"].append(
                    "Service recommended - diagnostic codes present"
                )
            else:
                safety_status["overall_status"] = "ok"
                safety_status["recommendations"].append("All safety systems operating normally")

            return safety_status

        except Exception as e:
            logger.error(f"Error validating Spartan K2 safety interlocks: {e}")
            return {"error": str(e)}

    def _initialize_system_health(self) -> None:
        """Initialize system health tracking."""
        for system_type in SpartanK2SystemType:
            self._system_health[system_type.value] = {
                "status": "unknown",
                "last_update": None,
                "message_count": 0,
                "error_count": 0,
            }

    def _update_system_health(self, message) -> None:
        """Update system health tracking based on decoded message."""
        system_key = message.system_type.value

        if system_key in self._system_health:
            health = self._system_health[system_key]
            health["last_update"] = message.timestamp
            health["message_count"] += 1

            # Update status based on safety interlocks and diagnostic codes
            if message.safety_interlocks:
                health["status"] = "violation"
                health["error_count"] += 1
            elif message.diagnostic_codes:
                health["status"] = "warning"
            else:
                health["status"] = "ok"
