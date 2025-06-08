"""
Firefly RV Systems Feature Module

This module provides a Feature class implementation for Firefly RV systems integration,
allowing it to be dynamically enabled/disabled and managed by the FeatureManager.

Integrates with the existing RVC feature system to provide:
- Firefly-specific protocol extensions
- Proprietary DGN handling
- Message multiplexing support
- Safety interlock monitoring
- CAN Detective integration (optional)
"""

import logging
from typing import Any

from backend.core.config import get_firefly_settings
from backend.services.feature_base import Feature

logger = logging.getLogger(__name__)


class FireflyFeature(Feature):
    """
    Firefly RV systems integration feature.

    This feature manages Firefly-specific extensions to the RV-C protocol, providing:
    - Proprietary DGN decoding and encoding
    - Multiplexed message handling
    - Safety interlock monitoring
    - Enhanced component control
    - Optional CAN Detective integration
    """

    def __init__(
        self,
        name: str = "firefly",
        enabled: bool = False,
        core: bool = False,
        config: dict[str, Any] | None = None,
        dependencies: list[str] | None = None,
        friendly_name: str | None = None,
    ):
        """
        Initialize the Firefly feature.

        Args:
            name: The name of the feature (default: "firefly")
            enabled: Whether the feature is enabled (default: False)
            core: Whether this is a core feature (default: False)
            config: Optional configuration dictionary
            dependencies: List of feature names this feature depends on
            friendly_name: Human-readable display name for the feature
        """
        super().__init__(
            name=name,
            enabled=enabled,
            core=core,
            config=config,
            dependencies=dependencies or ["rvc"],  # Firefly depends on RVC feature
            friendly_name=friendly_name or "Firefly RV Systems",
        )

        # Firefly components
        self.decoder = None
        self.encoder = None
        self.can_detective = None

        # Configuration from settings
        self.settings = get_firefly_settings()

        # Feature flags from configuration
        self._enable_multiplexing = self.settings.enable_multiplexing
        self._enable_custom_dgns = self.settings.enable_custom_dgns
        self._enable_state_interlocks = self.settings.enable_state_interlocks
        self._enable_can_detective = self.settings.enable_can_detective_integration

    async def startup(self) -> None:
        """
        Start the Firefly feature.

        This initializes the Firefly decoder, encoder, and optional components.
        """
        if not self.settings.enabled:
            logger.info("Firefly feature disabled in configuration")
            return

        logger.info("Starting Firefly feature")

        try:
            await self._initialize_firefly_components()
            logger.info("Firefly feature started successfully")
        except Exception as e:
            logger.error(f"Failed to start Firefly feature: {e}")
            raise

    async def shutdown(self) -> None:
        """
        Stop the Firefly feature and clean up components.
        """
        logger.info("Stopping Firefly feature")

        # Clean up components
        self.decoder = None
        self.encoder = None
        self.can_detective = None

    async def _initialize_firefly_components(self) -> None:
        """Initialize Firefly components based on configuration."""
        from backend.integrations.rvc.firefly_extensions import (
            FireflyCANDetectiveIntegration,
            FireflyDecoder,
            FireflyEncoder,
        )

        try:
            # Initialize Firefly Decoder
            self.decoder = FireflyDecoder(self.settings)
            logger.info("Firefly decoder initialized")

            # Initialize Firefly Encoder
            self.encoder = FireflyEncoder(self.settings)
            logger.info("Firefly encoder initialized")

            # Initialize CAN Detective integration if enabled
            if self._enable_can_detective:
                self.can_detective = FireflyCANDetectiveIntegration(self.settings)
                logger.info("Firefly CAN Detective integration initialized")

            logger.info("All Firefly components initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize Firefly components: {e}")
            # Continue operation with limited functionality
            self.decoder = None
            self.encoder = None
            self.can_detective = None
            raise

    def decode_message(
        self, dgn: int, source_address: int, data: bytes, timestamp: float, can_id: int
    ) -> dict[str, Any] | None:
        """
        Decode a message using Firefly extensions.

        Args:
            dgn: Data Group Number
            source_address: CAN source address
            data: Raw message data
            timestamp: Message timestamp
            can_id: Full CAN ID

        Returns:
            Decoded message data or None if not a Firefly message
        """
        if not self.decoder or not self.settings.enabled:
            return None

        try:
            firefly_message = self.decoder.decode_message(
                dgn, source_address, data, timestamp, can_id
            )

            if firefly_message:
                return {
                    "dgn": firefly_message.dgn,
                    "source_address": firefly_message.source_address,
                    "timestamp": firefly_message.timestamp,
                    "dgn_type": firefly_message.dgn_type.value,
                    "component_type": firefly_message.component_type.value
                    if firefly_message.component_type
                    else None,
                    "signals": firefly_message.signals,
                    "multiplexed_data": firefly_message.multiplexed_data,
                    "safety_status": firefly_message.safety_status.value
                    if firefly_message.safety_status
                    else None,
                    "validation_errors": firefly_message.validation_errors,
                    "firefly_specific": True,
                }
        except Exception as e:
            logger.error(f"Error decoding Firefly message: {e}")

        return None

    def encode_command(
        self,
        component: str,
        operation: str,
        parameters: dict[str, Any],
        validate_safety: bool = True,
    ) -> list[tuple[int, int, bytes]]:
        """
        Encode a command using Firefly extensions.

        Args:
            component: Component to control
            operation: Operation to perform
            parameters: Operation parameters
            validate_safety: Whether to validate safety interlocks

        Returns:
            List of (dgn, source_address, data) tuples for transmission
        """
        if not self.encoder or not self.settings.enabled:
            return []

        try:
            return self.encoder.encode_command(component, operation, parameters, validate_safety)
        except Exception as e:
            logger.error(f"Error encoding Firefly command: {e}")
            return []

    def validate_safety_interlocks(self, component: str, operation: str) -> tuple[bool, list[str]]:
        """
        Validate safety interlocks for a component operation.

        Args:
            component: Component name
            operation: Operation type

        Returns:
            Tuple of (is_safe, list_of_violations)
        """
        if not self.decoder or not self.settings.enabled:
            return True, []

        try:
            return self.decoder.validate_safety_interlocks(component, operation)
        except Exception as e:
            logger.error(f"Error validating safety interlocks: {e}")
            return False, [f"Safety validation error: {e}"]

    def update_vehicle_state(self, component: str, state_data: dict[str, Any]) -> None:
        """
        Update vehicle state for safety interlock checking.

        Args:
            component: Component name
            state_data: State data to update
        """
        if self.decoder and self.settings.enabled:
            try:
                self.decoder.update_vehicle_state(component, state_data)
            except Exception as e:
                logger.error(f"Error updating vehicle state: {e}")

    def analyze_message_patterns(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Analyze message patterns using CAN Detective integration.

        Args:
            messages: List of message dictionaries

        Returns:
            Analysis results
        """
        if not self.can_detective or not self.settings.enabled:
            return {}

        try:
            # Convert message dicts to FireflyMessage objects for analysis
            from backend.integrations.rvc.firefly_extensions import FireflyDGNType, FireflyMessage

            firefly_messages = []
            for msg_dict in messages:
                if msg_dict.get("firefly_specific"):
                    firefly_msg = FireflyMessage(
                        dgn=msg_dict["dgn"],
                        source_address=msg_dict["source_address"],
                        data=bytes.fromhex(msg_dict.get("data_hex", "")),
                        timestamp=msg_dict["timestamp"],
                        dgn_type=FireflyDGNType(msg_dict.get("dgn_type", "standard")),
                    )
                    firefly_messages.append(firefly_msg)

            return self.can_detective.analyze_message_pattern(firefly_messages)
        except Exception as e:
            logger.error(f"Error analyzing message patterns: {e}")
            return {}

    def export_can_detective_format(self, messages: list[dict[str, Any]]) -> str:
        """
        Export messages in CAN Detective compatible format.

        Args:
            messages: List of message dictionaries

        Returns:
            CAN Detective format string
        """
        if not self.can_detective or not self.settings.enabled:
            return ""

        try:
            # Convert message dicts to FireflyMessage objects for export
            from backend.integrations.rvc.firefly_extensions import FireflyDGNType, FireflyMessage

            firefly_messages = []
            for msg_dict in messages:
                if msg_dict.get("firefly_specific"):
                    firefly_msg = FireflyMessage(
                        dgn=msg_dict["dgn"],
                        source_address=msg_dict["source_address"],
                        data=bytes.fromhex(msg_dict.get("data_hex", "")),
                        timestamp=msg_dict["timestamp"],
                        dgn_type=FireflyDGNType(msg_dict.get("dgn_type", "standard")),
                    )
                    firefly_messages.append(firefly_msg)

            return self.can_detective.export_can_detective_format(firefly_messages)
        except Exception as e:
            logger.error(f"Error exporting CAN Detective format: {e}")
            return ""

    @property
    def health(self) -> str:
        """
        Returns the health status of the Firefly feature.

        Returns:
            - "healthy": Feature is functioning correctly
            - "degraded": Feature has non-critical issues
            - "failed": Feature is not functioning correctly
        """
        if not self.enabled:
            return "healthy"  # Disabled is considered healthy

        if not self.settings.enabled:
            return "healthy"  # Disabled in configuration is healthy

        # Check component health
        component_issues = 0

        if not self.decoder:
            component_issues += 1
        if not self.encoder:
            component_issues += 1
        if self._enable_can_detective and not self.can_detective:
            component_issues += 1

        # Decoder and encoder are critical components
        if not self.decoder or not self.encoder:
            return "degraded"

        # Multiple component failures indicate degraded state
        if component_issues > 1:
            return "degraded"

        return "healthy"

    def get_component_status(self) -> dict[str, Any]:
        """
        Get detailed status of all Firefly components.

        Returns:
            Dictionary with component status information
        """
        return {
            "enabled": self.enabled,
            "settings_enabled": self.settings.enabled,
            "configuration": {
                "multiplexing_enabled": self._enable_multiplexing,
                "custom_dgns_enabled": self._enable_custom_dgns,
                "safety_interlocks_enabled": self._enable_state_interlocks,
                "can_detective_enabled": self._enable_can_detective,
                "default_interface": self.settings.default_interface,
                "supported_components": self.settings.supported_components,
            },
            "components": {
                "decoder": {
                    "available": self.decoder is not None,
                    "status": self.decoder.get_decoder_status() if self.decoder else None,
                },
                "encoder": {
                    "available": self.encoder is not None,
                    "settings": {"safety_validation_enabled": self.settings.enable_state_interlocks}
                    if self.encoder
                    else None,
                },
                "can_detective": {
                    "enabled": self._enable_can_detective,
                    "available": self.can_detective is not None,
                    "integration_status": self.can_detective.enabled
                    if self.can_detective
                    else False,
                },
            },
            "safety_interlocks": {
                "enabled": self._enable_state_interlocks,
                "components": self.settings.safety_interlock_components,
                "required_interlocks": self.settings.required_interlocks,
            },
            "performance": {
                "priority_dgns": [f"0x{dgn:04X}" for dgn in self.settings.priority_dgns],
                "background_dgns": [f"0x{dgn:04X}" for dgn in self.settings.background_dgns],
                "multiplex_buffer_size": self.settings.multiplex_buffer_size,
                "multiplex_timeout_ms": self.settings.multiplex_timeout_ms,
            },
        }

    def get_supported_components(self) -> list[str]:
        """Get list of components supported by Firefly integration."""
        return self.settings.supported_components.copy()

    def get_firefly_dgn_ranges(self) -> dict[str, Any]:
        """Get Firefly-specific DGN range information."""
        return {
            "custom_range": {
                "start": f"0x{self.settings.custom_dgn_range_start:04X}",
                "end": f"0x{self.settings.custom_dgn_range_end:04X}",
                "count": self.settings.custom_dgn_range_end
                - self.settings.custom_dgn_range_start
                + 1,
            },
            "priority_dgns": [f"0x{dgn:04X}" for dgn in self.settings.priority_dgns],
            "background_dgns": [f"0x{dgn:04X}" for dgn in self.settings.background_dgns],
        }

    def get_safety_interlock_status(self) -> dict[str, Any]:
        """Get current safety interlock status."""
        if not self.decoder or not self.settings.enabled:
            return {"enabled": False, "message": "Firefly feature not available"}

        try:
            decoder_status = self.decoder.get_decoder_status()
            return {
                "enabled": self._enable_state_interlocks,
                "interlocks": decoder_status.get("safety_interlocks", {}),
                "component_states": list(self.decoder.component_states.keys())
                if hasattr(self.decoder, "component_states")
                else [],
            }
        except Exception as e:
            logger.error(f"Error getting safety interlock status: {e}")
            return {"enabled": False, "error": str(e)}
