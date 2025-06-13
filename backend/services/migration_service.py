"""
Migration Service for CAN Bus Decoder V2 Architecture

Provides service-level integration for the migration manager with the
main application, including configuration, monitoring, and API endpoints.
"""

import asyncio
import logging
from typing import Any

from backend.core.config import get_settings
# Mock dependencies - these would be replaced with actual implementations
from backend.core.migration_manager import MigrationManager, MigrationPhase
from backend.integrations.can.protocol_router import CANFrame
from backend.services.feature_manager import get_feature_manager

logger = logging.getLogger(__name__)


class MigrationService:
    """
    Service wrapper for migration manager with application integration.

    Handles feature flag integration, automatic phase advancement,
    and monitoring integration.
    """

    def __init__(self):
        self.migration_manager: MigrationManager | None = None
        self.feature_manager = get_feature_manager()
        self.settings = get_settings()
        self._monitoring_task: asyncio.Task | None = None
        self._is_initialized = False

    async def initialize(self) -> None:
        """Initialize migration service with dependencies."""
        if self._is_initialized:
            return

        # Check if migration feature is enabled
        if not self._is_migration_enabled():
            logger.info("Migration feature disabled - using legacy decoder only")
            return

        try:
            # Get dependencies - mock implementations for now
            performance_monitor = self._create_mock_performance_monitor()
            safety_engine = self._create_mock_safety_engine()

            # Create mock decoders for now - these would be replaced with actual implementations
            legacy_decoder = self._create_legacy_decoder()
            v2_decoder = self._create_v2_decoder()

            # Initialize migration manager
            self.migration_manager = MigrationManager(
                settings=self.settings,
                legacy_decoder=legacy_decoder,
                v2_decoder=v2_decoder,
                performance_monitor=performance_monitor,
                safety_engine=safety_engine,
            )

            # Start monitoring task
            self._monitoring_task = asyncio.create_task(self._monitoring_loop())

            self._is_initialized = True
            logger.info("Migration service initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize migration service: {e}")
            raise

    async def shutdown(self) -> None:
        """Shutdown migration service and cleanup resources."""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass

        self._is_initialized = False
        logger.info("Migration service shutdown complete")

    async def process_message(
        self,
        frame: CANFrame,
        vehicle_id: str | None = None
    ) -> Any:
        """
        Process CAN message through migration strategy.

        Args:
            frame: CAN frame to process
            vehicle_id: Optional vehicle identifier

        Returns:
            ProcessedMessage or None
        """
        if not self._is_initialized or not self.migration_manager:
            # Fallback to legacy processing
            return await self._process_legacy_only(frame)

        try:
            return await self.migration_manager.process_with_migration(frame, vehicle_id)
        except Exception as e:
            logger.error(f"Migration processing error: {e}")
            # Fallback to legacy on error
            return await self._process_legacy_only(frame)

    def get_migration_status(self) -> dict[str, Any]:
        """Get current migration status and metrics."""
        if not self._is_initialized or not self.migration_manager:
            return {
                "enabled": False,
                "phase": "disabled",
                "message": "Migration feature not enabled or not initialized"
            }

        status = self.migration_manager.get_migration_status()
        status["enabled"] = True
        status["feature_flags"] = self._get_migration_feature_flags()

        return status

    def advance_migration_phase(self) -> dict[str, Any]:
        """Manually advance migration phase if conditions are met."""
        if not self._is_initialized or not self.migration_manager:
            return {"success": False, "message": "Migration not initialized"}

        current_phase = self.migration_manager.current_phase
        success = self.migration_manager.advance_migration_phase()
        new_phase = self.migration_manager.current_phase

        if success:
            logger.info(f"Migration phase advanced: {current_phase.value} -> {new_phase.value}")
            return {
                "success": True,
                "previous_phase": current_phase.value,
                "new_phase": new_phase.value,
                "message": f"Advanced to {new_phase.value} phase"
            }
        else:
            return {
                "success": False,
                "current_phase": current_phase.value,
                "message": "Conditions not met for phase advancement"
            }

    def enroll_vehicle(self, vehicle_id: str) -> dict[str, Any]:
        """Enroll vehicle in V2 decoder usage."""
        if not self._is_initialized or not self.migration_manager:
            return {"success": False, "message": "Migration not initialized"}

        success = self.migration_manager.enroll_vehicle(vehicle_id)

        if success:
            return {
                "success": True,
                "vehicle_id": vehicle_id,
                "phase": self.migration_manager.current_phase.value,
                "message": f"Vehicle {vehicle_id} enrolled successfully"
            }
        else:
            return {
                "success": False,
                "vehicle_id": vehicle_id,
                "message": f"Failed to enroll vehicle {vehicle_id}"
            }

    async def _monitoring_loop(self) -> None:
        """Background monitoring loop for automatic phase advancement."""
        logger.info("Starting migration monitoring loop")

        try:
            while True:
                await asyncio.sleep(60)  # Check every minute

                if not self.migration_manager:
                    continue

                # Check for automatic phase advancement
                current_phase = self.migration_manager.current_phase

                # Auto-advance if conditions are met
                if current_phase == MigrationPhase.DISABLED:
                    if self._should_auto_advance_to_validation():
                        self.migration_manager.advance_migration_phase()
                        logger.info("Auto-advanced to validation phase")

                elif current_phase == MigrationPhase.VALIDATION:
                    if self._should_auto_advance_to_limited():
                        self.migration_manager.advance_migration_phase()
                        logger.info("Auto-advanced to limited rollout phase")

                # Monitor system health
                await self._check_system_health()

        except asyncio.CancelledError:
            logger.info("Migration monitoring loop cancelled")
            raise
        except Exception as e:
            logger.error(f"Error in migration monitoring loop: {e}")

    def _should_auto_advance_to_validation(self) -> bool:
        """Check if system should auto-advance to validation phase."""
        # Only auto-advance if explicitly configured
        return getattr(self.settings, "canbus_decoder_v2", {}).get("auto_advance_validation", False)

    def _should_auto_advance_to_limited(self) -> bool:
        """Check if system should auto-advance to limited rollout."""
        # Only auto-advance if explicitly configured and sufficient validation
        if not getattr(self.settings, "canbus_decoder_v2", {}).get("auto_advance_limited", False):
            return False

        if not self.migration_manager:
            return False

        # Require significant validation data before auto-advancing
        return self.migration_manager.total_validations >= 10000

    async def _check_system_health(self) -> None:
        """Monitor system health and trigger rollback if needed."""
        if not self.migration_manager:
            return

        # Get recent validation metrics
        recent_metrics = self.migration_manager.validation_metrics[-10:]
        if not recent_metrics:
            return

        # Check for concerning patterns
        error_rate = sum(
            1 for m in recent_metrics
            if m.validation_result.value == "error"
        ) / len(recent_metrics)

        if error_rate > 0.5:  # 50% error rate
            logger.warning(f"High error rate detected in validation: {error_rate:.1%}")

    def _is_migration_enabled(self) -> bool:
        """Check if migration feature is enabled via feature flags."""
        try:
            features = self.feature_manager.get_enabled_features()
            return (
                "canbus_decoder_v2" in features and
                features["canbus_decoder_v2"].get("enabled", False)
            )
        except Exception as e:
            logger.error(f"Error checking migration feature flag: {e}")
            return False

    def _get_migration_feature_flags(self) -> dict[str, Any]:
        """Get current migration-related feature flags."""
        try:
            features = self.feature_manager.get_enabled_features()
            return features.get("canbus_decoder_v2", {})
        except Exception as e:
            logger.error(f"Error getting migration feature flags: {e}")
            return {}

    def _create_legacy_decoder(self):
        """Create legacy decoder instance - placeholder implementation."""
        # This would be replaced with actual legacy decoder
        class MockLegacyDecoder:
            async def process_message(self, frame):
                # Simulate legacy processing
                await asyncio.sleep(0.005)  # 5ms processing time
                from backend.integrations.can.protocol_router import ProcessedMessage
                from backend.integrations.rvc.decoder_core import DecodedValue

                return ProcessedMessage(
                    pgn=frame.pgn,
                    source_address=frame.source_address,
                    decoded_data={"legacy_signal": DecodedValue(value=1, unit="legacy")},
                    errors=[],
                    processing_time_ms=5.0,
                    protocol="Legacy",
                    safety_events=[],
                )

        return MockLegacyDecoder()

    def _create_v2_decoder(self):
        """Create V2 decoder instance - placeholder implementation."""
        # This would be replaced with actual V2 decoder
        class MockV2Decoder:
            async def process_message(self, frame):
                # Simulate V2 processing (faster)
                await asyncio.sleep(0.002)  # 2ms processing time
                from backend.integrations.can.protocol_router import ProcessedMessage
                from backend.integrations.rvc.decoder_core import DecodedValue

                return ProcessedMessage(
                    pgn=frame.pgn,
                    source_address=frame.source_address,
                    decoded_data={"v2_signal": DecodedValue(value=2, unit="v2")},
                    errors=[],
                    processing_time_ms=2.0,
                    protocol="V2",
                    safety_events=[],
                )

        return MockV2Decoder()

    def _create_mock_performance_monitor(self):
        """Create mock performance monitor."""
        class MockPerformanceMonitor:
            def record_processing_time(self, component, duration):
                pass

        return MockPerformanceMonitor()

    def _create_mock_safety_engine(self):
        """Create mock safety engine."""
        class MockSafetyEngine:
            def __init__(self):
                from unittest.mock import Mock
                self.current_state = Mock()
                self.current_state.value = "parked_safe"

        return MockSafetyEngine()

    async def _process_legacy_only(self, frame):
        """Fallback legacy processing when migration is disabled."""
        # This would integrate with existing legacy decoder
        logger.debug("Processing with legacy decoder only")

        # Simulate legacy processing
        await asyncio.sleep(0.005)

        from backend.integrations.can.protocol_router import ProcessedMessage
        from backend.integrations.rvc.decoder_core import DecodedValue

        return ProcessedMessage(
            pgn=frame.pgn,
            source_address=frame.source_address,
            decoded_data={"legacy_only": DecodedValue(value=0, unit="legacy")},
            errors=[],
            processing_time_ms=5.0,
            protocol="Legacy",
            safety_events=[],
        )


# Global migration service instance
_migration_service: MigrationService | None = None


def get_migration_service() -> MigrationService:
    """Get global migration service instance."""
    global _migration_service
    if _migration_service is None:
        _migration_service = MigrationService()
    return _migration_service


async def initialize_migration_service() -> None:
    """Initialize global migration service."""
    service = get_migration_service()
    await service.initialize()


async def shutdown_migration_service() -> None:
    """Shutdown global migration service."""
    global _migration_service
    if _migration_service:
        await _migration_service.shutdown()
        _migration_service = None
