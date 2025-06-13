"""
Unit tests for Migration Manager.

Tests the migration manager functionality including phase advancement,
parallel processing validation, vehicle enrollment, and rollback mechanisms.
"""

import asyncio
import time
from unittest.mock import AsyncMock, Mock

import pytest

from backend.core.migration_manager import (
    MigrationManager,
    MigrationMetrics,
    MigrationPhase,
    ValidationResult,
    VehicleEnrollment,
)
from backend.integrations.can.protocol_router import CANFrame, ProcessedMessage
from backend.integrations.rvc.decoder_core import DecodedValue


class TestMigrationManager:
    """Test migration manager core functionality."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings object."""
        settings = Mock()
        settings.canbus_decoder_v2 = {
            "enabled": True,
            "auto_advance_validation": False,
            "auto_advance_limited": False,
        }
        return settings

    @pytest.fixture
    def mock_legacy_decoder(self):
        """Mock legacy decoder."""
        decoder = AsyncMock()
        decoder.process_message.return_value = ProcessedMessage(
            pgn=0x1FED1,
            source_address=0x42,
            decoded_data={"legacy_signal": DecodedValue(value=1, unit="legacy")},
            errors=[],
            processing_time_ms=5.0,
            protocol="Legacy",
            safety_events=[],
        )
        return decoder

    @pytest.fixture
    def mock_v2_decoder(self):
        """Mock V2 decoder."""
        decoder = AsyncMock()
        decoder.process_message.return_value = ProcessedMessage(
            pgn=0x1FED1,
            source_address=0x42,
            decoded_data={"v2_signal": DecodedValue(value=2, unit="v2")},
            errors=[],
            processing_time_ms=2.0,
            protocol="V2",
            safety_events=[],
        )
        return decoder

    @pytest.fixture
    def mock_performance_monitor(self):
        """Mock performance monitor."""
        monitor = Mock()
        monitor.get_system_health.return_value = {"overall": "healthy"}
        monitor.record_processing_time = Mock()
        return monitor

    @pytest.fixture
    def mock_safety_engine(self):
        """Mock safety engine."""
        engine = Mock()
        engine.current_state.value = "parked_safe"
        return engine

    @pytest.fixture
    def migration_manager(
        self,
        mock_settings,
        mock_legacy_decoder,
        mock_v2_decoder,
        mock_performance_monitor,
        mock_safety_engine,
    ):
        """Create migration manager with mocked dependencies."""
        return MigrationManager(
            settings=mock_settings,
            legacy_decoder=mock_legacy_decoder,
            v2_decoder=mock_v2_decoder,
            performance_monitor=mock_performance_monitor,
            safety_engine=mock_safety_engine,
        )

    @pytest.fixture
    def test_can_frame(self):
        """Create test CAN frame."""
        return CANFrame(
            arbitration_id=0x1FED142,
            pgn=0x1FED1,
            source_address=0x42,
            destination_address=0xFF,
            data=b"\\x00\\x00\\x01\\x00\\x00\\x00\\x00\\x00",
            timestamp=time.time(),
            is_extended=True,
        )

    async def test_initial_state_disabled(self, migration_manager):
        """Test migration manager starts in disabled state."""
        assert migration_manager.current_phase == MigrationPhase.DISABLED
        assert migration_manager.total_validations == 0
        assert len(migration_manager.vehicle_enrollments) == 0

    async def test_process_message_disabled_phase(
        self, migration_manager, mock_legacy_decoder, test_can_frame
    ):
        """Test message processing in disabled phase uses legacy only."""
        result = await migration_manager.process_with_migration(test_can_frame)

        assert result is not None
        assert result.protocol == "Legacy"
        mock_legacy_decoder.process_message.assert_called_once_with(test_can_frame)

    async def test_advance_to_validation_phase(self, migration_manager):
        """Test advancing from disabled to validation phase."""
        success = migration_manager.advance_migration_phase()

        assert success
        assert migration_manager.current_phase == MigrationPhase.VALIDATION

    async def test_parallel_validation_processing(
        self, migration_manager, mock_legacy_decoder, mock_v2_decoder, test_can_frame
    ):
        """Test parallel processing in validation phase."""
        # Advance to validation phase
        migration_manager.current_phase = MigrationPhase.VALIDATION

        result = await migration_manager.process_with_migration(test_can_frame, "test_vehicle")

        # Should return legacy result during validation
        assert result is not None
        assert result.protocol == "Legacy"

        # Both decoders should be called
        mock_legacy_decoder.process_message.assert_called_once()
        mock_v2_decoder.process_message.assert_called_once()

        # Validation metrics should be recorded
        assert migration_manager.total_validations == 1
        assert len(migration_manager.validation_metrics) == 1

    async def test_validation_metrics_comparison(self, migration_manager, test_can_frame):
        """Test validation metrics generation and comparison."""
        migration_manager.current_phase = MigrationPhase.VALIDATION

        # Process message to generate metrics
        await migration_manager.process_with_migration(test_can_frame)

        metrics = migration_manager.validation_metrics[0]
        assert isinstance(metrics, MigrationMetrics)
        assert metrics.legacy_processing_time == 5.0
        assert metrics.v2_processing_time == 2.0
        assert metrics.performance_delta < 0  # V2 is faster
        assert metrics.validation_result == ValidationResult.PERFORMANCE_IMPROVEMENT

    async def test_vehicle_enrollment(self, migration_manager):
        """Test vehicle enrollment in limited rollout phase."""
        migration_manager.current_phase = MigrationPhase.LIMITED_ROLLOUT

        success = migration_manager.enroll_vehicle("test_vehicle_001")

        assert success
        assert "test_vehicle_001" in migration_manager.vehicle_enrollments
        assert isinstance(migration_manager.vehicle_enrollments["test_vehicle_001"], VehicleEnrollment)

    async def test_vehicle_enrollment_wrong_phase(self, migration_manager):
        """Test vehicle enrollment fails in wrong phase."""
        migration_manager.current_phase = MigrationPhase.DISABLED

        success = migration_manager.enroll_vehicle("test_vehicle_001")

        assert not success
        assert "test_vehicle_001" not in migration_manager.vehicle_enrollments

    async def test_enrolled_vehicle_processing(
        self, migration_manager, mock_v2_decoder, test_can_frame
    ):
        """Test enrolled vehicle uses V2 decoder."""
        migration_manager.current_phase = MigrationPhase.LIMITED_ROLLOUT
        migration_manager.enroll_vehicle("test_vehicle")

        result = await migration_manager.process_with_migration(test_can_frame, "test_vehicle")

        assert result is not None
        assert result.protocol == "V2"
        mock_v2_decoder.process_message.assert_called_once()

    async def test_non_enrolled_vehicle_processing(
        self, migration_manager, mock_legacy_decoder, test_can_frame
    ):
        """Test non-enrolled vehicle uses legacy decoder."""
        migration_manager.current_phase = MigrationPhase.LIMITED_ROLLOUT

        result = await migration_manager.process_with_migration(test_can_frame, "non_enrolled_vehicle")

        assert result is not None
        assert result.protocol == "Legacy"
        mock_legacy_decoder.process_message.assert_called_once()

    async def test_rollback_on_safety_difference(self, migration_manager, test_can_frame):
        """Test automatic rollback on safety event differences."""
        migration_manager.current_phase = MigrationPhase.VALIDATION

        # Mock decoders to return different safety events
        migration_manager.legacy_decoder.process_message.return_value = ProcessedMessage(
            pgn=0x1FED1,
            source_address=0x42,
            decoded_data={},
            errors=[],
            processing_time_ms=5.0,
            protocol="Legacy",
            safety_events=["PARKING_BRAKE_SET"],
        )

        migration_manager.v2_decoder.process_message.return_value = ProcessedMessage(
            pgn=0x1FED1,
            source_address=0x42,
            decoded_data={},
            errors=[],
            processing_time_ms=2.0,
            protocol="V2",
            safety_events=["PARKING_BRAKE_RELEASED"],  # Different safety event
        )

        initial_phase = migration_manager.current_phase
        await migration_manager.process_with_migration(test_can_frame)

        # Should trigger rollback due to safety difference
        assert migration_manager.current_phase != initial_phase
        assert migration_manager.rollback_events > 0

    async def test_phase_advancement_conditions(self, migration_manager):
        """Test phase advancement condition checking."""
        # Start in disabled
        assert migration_manager.current_phase == MigrationPhase.DISABLED

        # Should be able to advance to validation
        assert migration_manager._can_advance_to_validation()
        migration_manager.advance_migration_phase()
        assert migration_manager.current_phase == MigrationPhase.VALIDATION

        # Cannot advance without sufficient validations
        assert not migration_manager._can_advance_to_limited_rollout()

        # Simulate successful validations
        for _ in range(1000):
            metrics = MigrationMetrics(
                validation_result=ValidationResult.PERFORMANCE_IMPROVEMENT,
                performance_delta=-0.5,  # 50% improvement
            )
            migration_manager.validation_metrics.append(metrics)
            migration_manager.total_validations += 1
            migration_manager.successful_validations += 1

        # Now should be able to advance
        assert migration_manager._can_advance_to_limited_rollout()

    async def test_migration_status_reporting(self, migration_manager):
        """Test comprehensive migration status reporting."""
        # Add some test data
        migration_manager.current_phase = MigrationPhase.VALIDATION
        migration_manager.total_validations = 100
        migration_manager.successful_validations = 95
        migration_manager.enroll_vehicle = Mock(return_value=True)

        status = migration_manager.get_migration_status()

        assert status["current_phase"] == "validation"
        assert status["validation_stats"]["total_validations"] == 100
        assert status["validation_stats"]["success_rate"] == 0.95
        assert "vehicle_enrollment" in status
        assert "performance_metrics" in status
        assert "can_advance" in status

    async def test_vehicle_unenrollment_on_errors(self, migration_manager, test_can_frame):
        """Test vehicle unenrollment after excessive errors."""
        migration_manager.current_phase = MigrationPhase.LIMITED_ROLLOUT
        migration_manager.enroll_vehicle("error_prone_vehicle")

        # Mock V2 decoder to throw exceptions
        migration_manager.v2_decoder.process_message.side_effect = Exception("V2 decoder error")

        vehicle_id = "error_prone_vehicle"
        for _ in range(migration_manager.consecutive_failures_threshold + 1):
            await migration_manager.process_with_migration(test_can_frame, vehicle_id)

        # Vehicle should be unenrolled due to excessive errors
        assert vehicle_id not in migration_manager.vehicle_enrollments

    async def test_complete_migration_phase(self, migration_manager, mock_v2_decoder, test_can_frame):
        """Test processing in complete migration phase."""
        migration_manager.current_phase = MigrationPhase.COMPLETE

        result = await migration_manager.process_with_migration(test_can_frame)

        assert result is not None
        assert result.protocol == "V2"
        mock_v2_decoder.process_message.assert_called_once()

    async def test_performance_monitoring_integration(self, migration_manager, test_can_frame):
        """Test integration with performance monitoring."""
        migration_manager.current_phase = MigrationPhase.LIMITED_ROLLOUT
        migration_manager.enroll_vehicle("monitored_vehicle")

        await migration_manager.process_with_migration(test_can_frame, "monitored_vehicle")

        # Performance monitor should record processing time
        migration_manager.performance_monitor.record_processing_time.assert_called_once()

    async def test_error_handling_graceful_fallback(self, migration_manager, test_can_frame):
        """Test graceful fallback to legacy on errors."""
        migration_manager.current_phase = MigrationPhase.VALIDATION

        # Mock both decoders to throw exceptions
        migration_manager.legacy_decoder.process_message.side_effect = Exception("Legacy error")
        migration_manager.v2_decoder.process_message.side_effect = Exception("V2 error")

        # Should not crash and handle exceptions gracefully
        result = await migration_manager.process_with_migration(test_can_frame)

        # Should still record validation attempt
        assert migration_manager.total_validations == 1


class TestVehicleEnrollment:
    """Test vehicle enrollment functionality."""

    def test_vehicle_enrollment_creation(self):
        """Test vehicle enrollment object creation."""
        enrollment = VehicleEnrollment(
            vehicle_id="test_001",
            enrollment_phase=MigrationPhase.LIMITED_ROLLOUT,
        )

        assert enrollment.vehicle_id == "test_001"
        assert enrollment.enrollment_phase == MigrationPhase.LIMITED_ROLLOUT
        assert enrollment.error_count == 0
        assert len(enrollment.validation_results) == 0

    def test_validation_result_tracking(self):
        """Test validation result tracking in enrollment."""
        enrollment = VehicleEnrollment("test_001", MigrationPhase.VALIDATION)

        # Add validation results
        for result in [
            ValidationResult.IDENTICAL,
            ValidationResult.PERFORMANCE_IMPROVEMENT,
            ValidationResult.MINOR_DIFFERENCE,
        ]:
            enrollment.update_validation_result(result)

        assert len(enrollment.validation_results) == 3
        assert enrollment.validation_results[-1] == ValidationResult.MINOR_DIFFERENCE

    def test_validation_result_limit(self):
        """Test validation result list size limit."""
        enrollment = VehicleEnrollment("test_001", MigrationPhase.VALIDATION)

        # Add more than the limit
        for i in range(150):
            enrollment.update_validation_result(ValidationResult.IDENTICAL)

        # Should be limited to 100
        assert len(enrollment.validation_results) == 100


class TestMigrationMetrics:
    """Test migration metrics functionality."""

    def test_metrics_creation(self):
        """Test migration metrics object creation."""
        metrics = MigrationMetrics(
            legacy_processing_time=5.0,
            v2_processing_time=2.0,
            performance_delta=-0.6,
            validation_result=ValidationResult.PERFORMANCE_IMPROVEMENT,
        )

        assert metrics.legacy_processing_time == 5.0
        assert metrics.v2_processing_time == 2.0
        assert metrics.performance_delta == -0.6
        assert metrics.validation_result == ValidationResult.PERFORMANCE_IMPROVEMENT

    def test_metrics_defaults(self):
        """Test migration metrics default values."""
        metrics = MigrationMetrics()

        assert metrics.legacy_processing_time == 0.0
        assert metrics.v2_processing_time == 0.0
        assert metrics.performance_delta == 0.0
        assert metrics.validation_result == ValidationResult.IDENTICAL
        assert len(metrics.legacy_safety_events) == 0
        assert len(metrics.v2_safety_events) == 0
        assert metrics.safety_events_match
