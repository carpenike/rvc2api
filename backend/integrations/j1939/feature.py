"""
J1939 feature module for the feature management system.

This module provides a Feature class implementation for J1939 protocol integration,
allowing it to be dynamically enabled/disabled and managed by the FeatureManager.

Key features:
- J1939 protocol decoding for engine, transmission, and chassis systems
- Manufacturer-specific extensions (Cummins, Allison, Spartan)
- Security validation and monitoring
- Performance optimization and prioritization
- Protocol bridging with RV-C
"""

import logging
from typing import Any

from backend.services.feature_base import Feature
from backend.services.feature_models import SafetyClassification

logger = logging.getLogger(__name__)


class J1939Feature(Feature):
    """
    J1939 protocol integration feature.

    This feature manages the J1939 protocol integration, providing:
    - Decoding of J1939 messages from engine, transmission, and chassis systems
    - Manufacturer-specific extensions for Cummins and Allison systems
    - Security monitoring and validation
    - Performance optimization and prioritization
    - Protocol bridging with RV-C for unified entity management
    """

    def __init__(
        self,
        name: str = "j1939",
        enabled: bool = False,
        core: bool = False,
        config: dict[str, Any] | None = None,
        dependencies: list[str] | None = None,
        friendly_name: str | None = None,
        safety_classification: SafetyClassification | None = None,
        log_state_transitions: bool = True,
    ):
        """
        Initialize the J1939 feature.

        Args:
            name: The name of the feature (default: "j1939")
            enabled: Whether the feature is enabled (default: False)
            core: Whether this is a core feature (default: False)
            config: Optional configuration dictionary
            dependencies: List of feature names this feature depends on
            friendly_name: Human-readable display name for the feature
            safety_classification: Safety classification for state validation
            log_state_transitions: Whether to log state transitions for audit
        """
        super().__init__(
            name=name,
            enabled=enabled,
            core=core,
            config=config,
            dependencies=dependencies,
            friendly_name=friendly_name,
            safety_classification=safety_classification,
            log_state_transitions=log_state_transitions,
        )
        self.config = config or {}

        # J1939 components
        self.decoder = None
        self.validator = None
        self.security_manager = None
        self.performance_handler = None
        self.protocol_bridge = None

        # Configuration flags
        self._enable_cummins_extensions = self.config.get("enable_cummins_extensions", True)
        self._enable_allison_extensions = self.config.get("enable_allison_extensions", True)
        self._enable_chassis_extensions = self.config.get("enable_chassis_extensions", True)
        self._enable_validator = self.config.get("enable_validator", True)
        self._enable_security = self.config.get("enable_security", True)
        self._enable_performance = self.config.get("enable_performance", True)
        self._enable_rvc_bridge = self.config.get("enable_rvc_bridge", True)

        self._data_loaded = False

    async def startup(self) -> None:
        """
        Start the J1939 feature.

        This initializes the J1939 decoder and associated components.
        """
        logger.info("Starting J1939 feature")
        await self._initialize_j1939_components()

    async def shutdown(self) -> None:
        """
        Stop the J1939 feature and clean up components.
        """
        logger.info("Stopping J1939 feature")

        # Shutdown components
        if self.performance_handler:
            try:
                self.performance_handler.stop_processing()
            except Exception as e:
                logger.warning(f"Error stopping J1939 performance handler: {e}")

        if self.protocol_bridge:
            try:
                await self.protocol_bridge.shutdown()
            except Exception as e:
                logger.warning(f"Error shutting down J1939 protocol bridge: {e}")

        self.decoder = None
        self.validator = None
        self.security_manager = None
        self.performance_handler = None
        self.protocol_bridge = None
        self._data_loaded = False

    async def _initialize_j1939_components(self) -> None:
        """Initialize J1939 components."""
        from backend.core.config import get_settings

        settings = get_settings()

        # Check if J1939 is enabled in settings
        if not settings.j1939.enabled:
            logger.info("J1939 protocol is disabled in settings")
            return

        try:
            # Initialize J1939 Decoder
            from backend.integrations.j1939.decoder import J1939Decoder

            self.decoder = J1939Decoder(settings)
            logger.info("J1939 Decoder initialized")

            # Initialize Validator if enabled
            if self._enable_validator:
                try:
                    from backend.integrations.j1939.validator import J1939Validator

                    self.validator = J1939Validator(settings)
                    logger.info("J1939 Validator initialized")
                except ImportError:
                    logger.warning("J1939 Validator not available - skipping")

            # Initialize Security Manager if enabled
            if self._enable_security:
                try:
                    from backend.integrations.j1939.security import J1939SecurityManager

                    self.security_manager = J1939SecurityManager(settings)
                    logger.info("J1939 Security Manager initialized")
                except ImportError:
                    logger.warning("J1939 Security Manager not available - skipping")

            # Initialize Performance Handler if enabled
            if self._enable_performance:
                try:
                    from backend.integrations.j1939.performance import J1939PerformanceHandler

                    max_queue_size = self.config.get("max_queue_size", 10000)
                    self.performance_handler = J1939PerformanceHandler(settings, max_queue_size)
                    logger.info("J1939 Performance Handler initialized")
                except ImportError:
                    logger.warning("J1939 Performance Handler not available - skipping")

            # Initialize Protocol Bridge if enabled
            if self._enable_rvc_bridge:
                try:
                    from backend.integrations.j1939.bridge import J1939ProtocolBridge

                    self.protocol_bridge = J1939ProtocolBridge(settings)
                    await self.protocol_bridge.startup()
                    logger.info("J1939 Protocol Bridge initialized")
                except ImportError:
                    logger.warning("J1939 Protocol Bridge not available - skipping")

            self._data_loaded = True
            logger.info("J1939 components initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize J1939 components: {e}")
            # Continue operation with degraded functionality
            self.decoder = None
            self.validator = None
            self.security_manager = None
            self.performance_handler = None
            self.protocol_bridge = None
            self._data_loaded = False

    def is_data_loaded(self) -> bool:
        """
        Check if J1939 data is loaded.

        Returns:
            True if data is loaded, False otherwise
        """
        return self._data_loaded

    def decode_message(
        self,
        pgn: int,
        source_address: int,
        data: bytes,
        priority: int = 6,
        timestamp: float | None = None,
    ):
        """
        Decode a J1939 message using the initialized decoder.

        Args:
            pgn: Parameter Group Number
            source_address: Source address of the message
            data: Message data bytes
            priority: Message priority (0-7, lower is higher priority)
            timestamp: Optional timestamp

        Returns:
            Decoded J1939Message or None if decoding fails
        """
        if not self.decoder:
            return None

        return self.decoder.decode_message(pgn, source_address, data, priority, timestamp)

    def validate_message(
        self, pgn: int, source_address: int, data: bytes
    ) -> tuple[bool, list[str]]:
        """
        Validate a J1939 message.

        Args:
            pgn: Parameter Group Number
            source_address: Source address
            data: Message data bytes

        Returns:
            Tuple of (is_valid, validation_errors)
        """
        if not self.validator:
            return True, []  # Pass through if validator not available

        return self.validator.validate_message(pgn, source_address, data)

    def check_security(self, pgn: int, source_address: int, data: bytes) -> tuple[bool, list[str]]:
        """
        Check security aspects of a J1939 message.

        Args:
            pgn: Parameter Group Number
            source_address: Source address
            data: Message data bytes

        Returns:
            Tuple of (is_secure, security_warnings)
        """
        if not self.security_manager:
            return True, []  # Pass through if security manager not available

        return self.security_manager.check_message_security(pgn, source_address, data)

    @property
    def health(self) -> str:
        """
        Returns the health status of the feature including all components.

        Returns:
            - "healthy": Feature is functioning correctly
            - "degraded": Feature has non-critical issues
            - "failed": Feature is not functioning correctly
        """
        if not self.enabled:
            return "healthy"  # Disabled is considered healthy

        if not self.is_data_loaded():
            return "failed"

        # Check component health
        component_issues = 0
        critical_issues = 0

        if not self.decoder:
            critical_issues += 1  # Decoder is critical

        if self._enable_validator and not self.validator:
            component_issues += 1
        if self._enable_security and not self.security_manager:
            component_issues += 1
        if self._enable_performance and not self.performance_handler:
            component_issues += 1
        if self._enable_rvc_bridge and not self.protocol_bridge:
            component_issues += 1

        # Critical component failure means failed state
        if critical_issues > 0:
            return "failed"

        # Multiple component failures indicate degraded state
        if component_issues > 1:
            return "degraded"

        return "healthy"

    def get_component_status(self) -> dict[str, Any]:
        """
        Get detailed status of all J1939 components.

        Returns:
            Dictionary with component status information
        """
        decoder_info = None
        if self.decoder:
            try:
                decoder_info = {
                    "supported_pgns": len(self.decoder.get_supported_pgns()),
                    "cummins_enabled": self._enable_cummins_extensions,
                    "allison_enabled": self._enable_allison_extensions,
                    "chassis_enabled": self._enable_chassis_extensions,
                }
            except Exception as e:
                logger.warning(f"Error getting decoder info: {e}")

        validator_stats = None
        if self.validator:
            try:
                validator_stats = self.validator.get_validation_stats()
            except Exception as e:
                logger.warning(f"Error getting validator stats: {e}")

        security_status = None
        if self.security_manager:
            try:
                security_status = self.security_manager.get_security_status()
            except Exception as e:
                logger.warning(f"Error getting security status: {e}")

        performance_metrics = None
        if self.performance_handler:
            try:
                performance_metrics = self.performance_handler.get_performance_metrics()
            except Exception as e:
                logger.warning(f"Error getting performance metrics: {e}")

        bridge_status = None
        if self.protocol_bridge:
            try:
                bridge_status = self.protocol_bridge.get_bridge_status()
            except Exception as e:
                logger.warning(f"Error getting bridge status: {e}")

        return {
            "data_loaded": self.is_data_loaded(),
            "components": {
                "decoder": {
                    "enabled": True,
                    "available": self.decoder is not None,
                    "info": decoder_info,
                },
                "validator": {
                    "enabled": self._enable_validator,
                    "available": self.validator is not None,
                    "stats": validator_stats,
                },
                "security": {
                    "enabled": self._enable_security,
                    "available": self.security_manager is not None,
                    "status": security_status,
                },
                "performance": {
                    "enabled": self._enable_performance,
                    "available": self.performance_handler is not None,
                    "metrics": performance_metrics,
                },
                "protocol_bridge": {
                    "enabled": self._enable_rvc_bridge,
                    "available": self.protocol_bridge is not None,
                    "status": bridge_status,
                },
            },
        }
