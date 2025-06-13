"""
Migration Manager for CAN Bus Decoder V2 Architecture

Provides safe migration from legacy decoder to V2 architecture with:
- Parallel processing validation
- Performance delta monitoring
- Gradual vehicle enrollment
- Automatic rollback on safety violations

This is the final component of the CAN Bus Decoder V2 implementation.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol

from backend.core.config import Settings
from backend.core.safety_state_engine import SafetyStateEngine
from backend.integrations.can.performance_monitor import PerformanceMonitor
from backend.integrations.can.protocol_router import CANFrame, ProcessedMessage

logger = logging.getLogger(__name__)

# Constants
MAX_VALIDATION_RESULTS_HISTORY = 100


class MigrationPhase(Enum):
    """Migration phases for gradual rollout."""

    DISABLED = "disabled"
    VALIDATION = "validation"  # Parallel processing, legacy active
    LIMITED_ROLLOUT = "limited_rollout"  # V2 active for test vehicles
    PRODUCTION_ROLLOUT = "production_rollout"  # V2 active for production vehicles
    COMPLETE = "complete"  # Legacy system decommissioned


class ValidationResult(Enum):
    """Result of parallel processing validation."""

    IDENTICAL = "identical"
    MINOR_DIFFERENCE = "minor_difference"
    PERFORMANCE_IMPROVEMENT = "performance_improvement"
    SAFETY_DIFFERENCE = "safety_difference"
    ERROR = "error"


@dataclass
class MigrationMetrics:
    """Metrics for migration monitoring."""

    # Processing performance
    legacy_processing_time: float = 0.0
    v2_processing_time: float = 0.0
    performance_delta: float = 0.0

    # Safety validation
    legacy_safety_events: list[Any] = field(default_factory=list)
    v2_safety_events: list[Any] = field(default_factory=list)
    safety_events_match: bool = True

    # Error rates
    legacy_error_count: int = 0
    v2_error_count: int = 0

    # Validation result
    validation_result: ValidationResult = ValidationResult.IDENTICAL
    timestamp: float = field(default_factory=time.time)


class LegacyDecoder(Protocol):
    """Protocol for legacy decoder interface."""

    async def process_message(self, frame: CANFrame) -> ProcessedMessage | None:
        """Process message using legacy decoder."""
        ...


class V2Decoder(Protocol):
    """Protocol for V2 decoder interface."""

    async def process_message(self, frame: CANFrame) -> ProcessedMessage | None:
        """Process message using V2 decoder."""
        ...


@dataclass
class VehicleEnrollment:
    """Vehicle enrollment status for gradual rollout."""

    vehicle_id: str
    enrollment_phase: MigrationPhase
    enrollment_time: float = field(default_factory=time.time)
    validation_results: list[ValidationResult] = field(default_factory=list)
    error_count: int = 0
    last_activity: float = field(default_factory=time.time)

    def update_validation_result(self, result: ValidationResult) -> None:
        """Update validation result and maintain recent history."""
        self.validation_results.append(result)
        # Keep last MAX_VALIDATION_RESULTS_HISTORY results
        if len(self.validation_results) > MAX_VALIDATION_RESULTS_HISTORY:
            self.validation_results = self.validation_results[-MAX_VALIDATION_RESULTS_HISTORY:]
        self.last_activity = time.time()


class MigrationManager:
    """
    Manages safe migration from legacy to V2 CAN decoder architecture.

    Provides parallel processing validation, performance monitoring, gradual
    vehicle enrollment, and automatic rollback capabilities.
    """

    def __init__(
        self,
        settings: Settings,
        legacy_decoder: LegacyDecoder,
        v2_decoder: V2Decoder,
        performance_monitor: PerformanceMonitor,
        safety_engine: SafetyStateEngine,
    ):
        self.settings = settings
        self.legacy_decoder = legacy_decoder
        self.v2_decoder = v2_decoder
        self.performance_monitor = performance_monitor
        self.safety_engine = safety_engine

        # Migration state
        self.current_phase = MigrationPhase.DISABLED
        self.vehicle_enrollments: dict[str, VehicleEnrollment] = {}
        self.validation_metrics: list[MigrationMetrics] = []

        # Performance thresholds
        self.max_performance_degradation = 0.1  # 10% max degradation
        self.max_error_rate_increase = 0.01  # 1% max error rate increase
        self.min_safety_match_rate = 0.99  # 99% safety event match required

        # Rollback triggers
        self.consecutive_failures_threshold = 5
        self.error_rate_threshold = 0.05  # 5% error rate triggers rollback

        # Statistics
        self.total_validations = 0
        self.successful_validations = 0
        self.rollback_events = 0
        self.start_time = time.time()

        logger.info(
            f"Migration Manager initialized: phase={self.current_phase.value}, "
            f"performance_threshold={self.max_performance_degradation}, "
            f"safety_match_threshold={self.min_safety_match_rate}"
        )

    async def process_with_migration(
        self, frame: CANFrame, vehicle_id: str | None = None
    ) -> ProcessedMessage | None:
        """
        Process CAN frame with migration strategy.

        Routes to appropriate decoder based on migration phase and vehicle enrollment.
        Performs parallel validation when required.

        Args:
            frame: CAN frame to process
            vehicle_id: Optional vehicle identifier for enrollment tracking

        Returns:
            ProcessedMessage from active decoder, or None if processing failed
        """
        if self.current_phase == MigrationPhase.DISABLED:
            # Legacy only
            return await self.legacy_decoder.process_message(frame)

        elif self.current_phase == MigrationPhase.VALIDATION:
            # Parallel processing for validation
            return await self._parallel_validation(frame, vehicle_id)

        elif self.current_phase in [
            MigrationPhase.LIMITED_ROLLOUT,
            MigrationPhase.PRODUCTION_ROLLOUT,
        ]:
            # Route based on vehicle enrollment
            if vehicle_id and self._is_vehicle_enrolled(vehicle_id):
                return await self._process_with_rollback_protection(frame, vehicle_id)
            else:
                return await self.legacy_decoder.process_message(frame)

        elif self.current_phase == MigrationPhase.COMPLETE:
            # V2 only
            return await self.v2_decoder.process_message(frame)

        else:
            logger.error(f"Unknown migration phase: {self.current_phase}")
            return await self.legacy_decoder.process_message(frame)

    async def _parallel_validation(
        self, frame: CANFrame, vehicle_id: str | None
    ) -> ProcessedMessage | None:
        """Process frame with both decoders for validation comparison."""
        start_time = time.time()

        try:
            # Process with both decoders concurrently
            legacy_task = asyncio.create_task(self.legacy_decoder.process_message(frame))
            v2_task = asyncio.create_task(self.v2_decoder.process_message(frame))

            results = await asyncio.gather(legacy_task, v2_task, return_exceptions=True)

            legacy_result = results[0]
            v2_result = results[1]

            # Handle exceptions and type narrowing
            legacy_processed: ProcessedMessage | None = None
            v2_processed: ProcessedMessage | None = None

            if isinstance(legacy_result, Exception):
                logger.error(f"Legacy decoder error: {legacy_result}")
                legacy_processed = None
            elif isinstance(legacy_result, ProcessedMessage):
                legacy_processed = legacy_result
            else:
                legacy_processed = None

            if isinstance(v2_result, Exception):
                logger.error(f"V2 decoder error: {v2_result}")
                v2_processed = None
            elif isinstance(v2_result, ProcessedMessage):
                v2_processed = v2_result
            else:
                v2_processed = None

            # Compare results and update metrics
            metrics = await self._compare_processing_results(
                legacy_processed, v2_processed, start_time
            )

            self.validation_metrics.append(metrics)
            self.total_validations += 1

            # Update vehicle enrollment if provided
            if vehicle_id:
                self._update_vehicle_validation(vehicle_id, metrics.validation_result)

            # Check for rollback conditions
            if await self._should_trigger_rollback(metrics):
                await self._trigger_rollback("Validation failure detected")

            # Return legacy result during validation phase
            return legacy_processed

        except Exception as e:
            logger.error(f"Error in parallel validation: {e}")
            # Fallback to legacy on validation error
            return await self.legacy_decoder.process_message(frame)

    async def _process_with_rollback_protection(
        self, frame: CANFrame, vehicle_id: str
    ) -> ProcessedMessage | None:
        """Process with V2 decoder with rollback protection."""
        try:
            start_time = time.time()
            result = await self.v2_decoder.process_message(frame)

            # Monitor performance
            processing_time = time.time() - start_time
            self.performance_monitor.record_processing_time("migration_v2", processing_time)

            # Update vehicle activity
            if vehicle_id in self.vehicle_enrollments:
                self.vehicle_enrollments[vehicle_id].last_activity = time.time()

            return result

        except Exception as e:
            logger.error(f"V2 decoder error for vehicle {vehicle_id}: {e}")

            # Increment error count for vehicle
            if vehicle_id in self.vehicle_enrollments:
                self.vehicle_enrollments[vehicle_id].error_count += 1

                # Check if vehicle should be unenrolled
                if (
                    self.vehicle_enrollments[vehicle_id].error_count
                    > self.consecutive_failures_threshold
                ):
                    await self._unenroll_vehicle(vehicle_id, f"Excessive errors: {e}")

            # Fallback to legacy
            return await self.legacy_decoder.process_message(frame)

    async def _compare_processing_results(
        self,
        legacy_result: ProcessedMessage | None,
        v2_result: ProcessedMessage | None,
        start_time: float,
    ) -> MigrationMetrics:
        """Compare results from legacy and V2 decoders."""
        metrics = MigrationMetrics()

        # Calculate processing times
        if legacy_result:
            metrics.legacy_processing_time = legacy_result.processing_time_ms
        if v2_result:
            metrics.v2_processing_time = v2_result.processing_time_ms

        if metrics.legacy_processing_time > 0 and metrics.v2_processing_time > 0:
            metrics.performance_delta = (
                metrics.v2_processing_time - metrics.legacy_processing_time
            ) / metrics.legacy_processing_time

        # Compare safety events
        if legacy_result:
            metrics.legacy_safety_events = legacy_result.safety_events
        if v2_result:
            metrics.v2_safety_events = v2_result.safety_events

        metrics.safety_events_match = self._compare_safety_events(
            metrics.legacy_safety_events, metrics.v2_safety_events
        )

        # Count errors
        if legacy_result:
            metrics.legacy_error_count = len(legacy_result.errors)
        if v2_result:
            metrics.v2_error_count = len(v2_result.errors)

        # Determine validation result
        metrics.validation_result = self._assess_validation_result(metrics)

        if metrics.validation_result in [
            ValidationResult.IDENTICAL,
            ValidationResult.PERFORMANCE_IMPROVEMENT,
        ]:
            self.successful_validations += 1

        return metrics

    def _compare_safety_events(self, legacy_events: list, v2_events: list) -> bool:
        """Compare safety event lists for equivalence."""
        if len(legacy_events) != len(v2_events):
            return False

        # Convert to comparable format and sort
        legacy_set = set(str(event) for event in legacy_events)
        v2_set = set(str(event) for event in v2_events)

        return legacy_set == v2_set

    def _assess_validation_result(self, metrics: MigrationMetrics) -> ValidationResult:
        """Assess overall validation result based on metrics."""
        # Check for safety differences (highest priority)
        if not metrics.safety_events_match:
            return ValidationResult.SAFETY_DIFFERENCE

        # Check for errors
        if metrics.v2_error_count > metrics.legacy_error_count:
            return ValidationResult.ERROR

        # Check performance
        if metrics.performance_delta < -0.05:  # 5% improvement
            return ValidationResult.PERFORMANCE_IMPROVEMENT
        elif metrics.performance_delta > self.max_performance_degradation:
            return ValidationResult.MINOR_DIFFERENCE

        return ValidationResult.IDENTICAL

    async def _should_trigger_rollback(self, metrics: MigrationMetrics) -> bool:
        """Check if current metrics should trigger a rollback."""
        # Immediate rollback conditions
        if metrics.validation_result == ValidationResult.SAFETY_DIFFERENCE:
            logger.error("CRITICAL: Safety event mismatch detected")
            return True

        # Check recent error rate
        recent_metrics = self.validation_metrics[-20:]  # Last 20 validations
        if recent_metrics:
            error_rate = sum(
                1 for m in recent_metrics if m.validation_result == ValidationResult.ERROR
            ) / len(recent_metrics)

            if error_rate > self.error_rate_threshold:
                logger.warning(f"High error rate detected: {error_rate:.2%}")
                return True

        # Check consecutive failures
        if len(self.validation_metrics) >= self.consecutive_failures_threshold:
            recent_failures = all(
                m.validation_result in [ValidationResult.ERROR, ValidationResult.SAFETY_DIFFERENCE]
                for m in self.validation_metrics[-self.consecutive_failures_threshold :]
            )

            if recent_failures:
                logger.error("Consecutive validation failures detected")
                return True

        return False

    async def _trigger_rollback(self, reason: str) -> None:
        """Trigger emergency rollback to legacy system."""
        logger.error(f"TRIGGERING ROLLBACK: {reason}")

        self.rollback_events += 1
        previous_phase = self.current_phase

        # Revert to appropriate safe phase
        if self.current_phase == MigrationPhase.VALIDATION:
            self.current_phase = MigrationPhase.DISABLED
        elif self.current_phase in [
            MigrationPhase.LIMITED_ROLLOUT,
            MigrationPhase.PRODUCTION_ROLLOUT,
        ]:
            self.current_phase = MigrationPhase.VALIDATION

        # Unenroll all vehicles
        for vehicle_id in list(self.vehicle_enrollments.keys()):
            await self._unenroll_vehicle(vehicle_id, f"Rollback: {reason}")

        logger.error(f"Rollback complete: {previous_phase.value} -> {self.current_phase.value}")

    def advance_migration_phase(self) -> bool:
        """Advance to next migration phase if conditions are met."""
        if self.current_phase == MigrationPhase.DISABLED:
            if self._can_advance_to_validation():
                self.current_phase = MigrationPhase.VALIDATION
                logger.info("Advanced to VALIDATION phase")
                return True

        elif self.current_phase == MigrationPhase.VALIDATION:
            if self._can_advance_to_limited_rollout():
                self.current_phase = MigrationPhase.LIMITED_ROLLOUT
                logger.info("Advanced to LIMITED_ROLLOUT phase")
                return True

        elif self.current_phase == MigrationPhase.LIMITED_ROLLOUT:
            if self._can_advance_to_production():
                self.current_phase = MigrationPhase.PRODUCTION_ROLLOUT
                logger.info("Advanced to PRODUCTION_ROLLOUT phase")
                return True

        elif self.current_phase == MigrationPhase.PRODUCTION_ROLLOUT:
            if self._can_complete_migration():
                self.current_phase = MigrationPhase.COMPLETE
                logger.info("Migration COMPLETE - Legacy system can be decommissioned")
                return True

        return False

    def _can_advance_to_validation(self) -> bool:
        """Check if system is ready for validation phase."""
        # Basic system health checks - simplified for now
        return self.safety_engine.current_state.value != "unsafe"

    def _can_advance_to_limited_rollout(self) -> bool:
        """Check if validation results support limited rollout."""
        if self.total_validations < 1000:  # Need sufficient validation data
            return False

        success_rate = self.successful_validations / self.total_validations
        if success_rate < self.min_safety_match_rate:
            return False

        # Check recent performance
        recent_metrics = self.validation_metrics[-100:]
        avg_performance_delta = sum(m.performance_delta for m in recent_metrics) / len(
            recent_metrics
        )

        return avg_performance_delta <= self.max_performance_degradation

    def _can_advance_to_production(self) -> bool:
        """Check if limited rollout results support production rollout."""
        enrolled_vehicles = len(self.vehicle_enrollments)
        if enrolled_vehicles < 5:  # Need successful limited rollout
            return False

        # Check vehicle success rates
        successful_vehicles = sum(
            1
            for enrollment in self.vehicle_enrollments.values()
            if enrollment.error_count < self.consecutive_failures_threshold
        )

        success_rate = successful_vehicles / enrolled_vehicles
        return success_rate >= 0.95  # 95% vehicle success rate

    def _can_complete_migration(self) -> bool:
        """Check if system is ready for complete migration."""
        # Require significant production experience
        enrolled_vehicles = len(self.vehicle_enrollments)
        if enrolled_vehicles < 50:  # Substantial production fleet
            return False

        # Check system stability
        uptime_hours = (time.time() - self.start_time) / 3600.0
        if uptime_hours < 168:  # One week minimum
            return False

        return self.rollback_events == 0  # No recent rollbacks

    def enroll_vehicle(self, vehicle_id: str) -> bool:
        """Enroll vehicle in V2 decoder usage."""
        if self.current_phase not in [
            MigrationPhase.LIMITED_ROLLOUT,
            MigrationPhase.PRODUCTION_ROLLOUT,
        ]:
            logger.warning(
                f"Cannot enroll vehicle {vehicle_id} in phase {self.current_phase.value}"
            )
            return False

        if vehicle_id in self.vehicle_enrollments:
            logger.info(f"Vehicle {vehicle_id} already enrolled")
            return True

        self.vehicle_enrollments[vehicle_id] = VehicleEnrollment(
            vehicle_id=vehicle_id,
            enrollment_phase=self.current_phase,
        )

        logger.info(f"Enrolled vehicle {vehicle_id} in {self.current_phase.value}")
        return True

    async def _unenroll_vehicle(self, vehicle_id: str, reason: str) -> None:
        """Unenroll vehicle from V2 decoder usage."""
        if vehicle_id in self.vehicle_enrollments:
            enrollment = self.vehicle_enrollments.pop(vehicle_id)
            logger.warning(
                f"Unenrolled vehicle {vehicle_id}: {reason} "
                f"(enrolled for {(time.time() - enrollment.enrollment_time) / 3600:.1f} hours)"
            )

    def _is_vehicle_enrolled(self, vehicle_id: str) -> bool:
        """Check if vehicle is enrolled for V2 processing."""
        return vehicle_id in self.vehicle_enrollments

    def _update_vehicle_validation(self, vehicle_id: str, result: ValidationResult) -> None:
        """Update vehicle enrollment with validation result."""
        if vehicle_id not in self.vehicle_enrollments:
            # Auto-enroll in validation phase
            if self.current_phase == MigrationPhase.VALIDATION:
                self.vehicle_enrollments[vehicle_id] = VehicleEnrollment(
                    vehicle_id=vehicle_id,
                    enrollment_phase=self.current_phase,
                )

        if vehicle_id in self.vehicle_enrollments:
            self.vehicle_enrollments[vehicle_id].update_validation_result(result)

    def get_migration_status(self) -> dict[str, Any]:
        """Get comprehensive migration status."""
        uptime_hours = (time.time() - self.start_time) / 3600.0

        status = {
            "current_phase": self.current_phase.value,
            "uptime_hours": uptime_hours,
            "validation_stats": {
                "total_validations": self.total_validations,
                "successful_validations": self.successful_validations,
                "success_rate": self.successful_validations / max(self.total_validations, 1),
                "rollback_events": self.rollback_events,
            },
            "vehicle_enrollment": {
                "total_enrolled": len(self.vehicle_enrollments),
                "by_phase": {},
                "vehicles": {
                    vid: {
                        "enrollment_phase": enrollment.enrollment_phase.value,
                        "enrollment_hours": (time.time() - enrollment.enrollment_time) / 3600.0,
                        "error_count": enrollment.error_count,
                        "recent_validation_results": enrollment.validation_results[-10:],
                    }
                    for vid, enrollment in self.vehicle_enrollments.items()
                },
            },
            "performance_metrics": self._get_performance_summary(),
            "can_advance": {
                "to_validation": self._can_advance_to_validation(),
                "to_limited_rollout": self._can_advance_to_limited_rollout(),
                "to_production": self._can_advance_to_production(),
                "to_complete": self._can_complete_migration(),
            },
        }

        # Count vehicles by enrollment phase
        for enrollment in self.vehicle_enrollments.values():
            phase = enrollment.enrollment_phase.value
            status["vehicle_enrollment"]["by_phase"][phase] = (
                status["vehicle_enrollment"]["by_phase"].get(phase, 0) + 1
            )

        return status

    def _get_performance_summary(self) -> dict[str, Any]:
        """Get performance comparison summary."""
        if not self.validation_metrics:
            return {"message": "No validation data available"}

        recent_metrics = self.validation_metrics[-MAX_VALIDATION_RESULTS_HISTORY:]

        return {
            "average_performance_delta": sum(m.performance_delta for m in recent_metrics)
            / len(recent_metrics),
            "safety_match_rate": sum(1 for m in recent_metrics if m.safety_events_match)
            / len(recent_metrics),
            "validation_results": {
                result.value: sum(1 for m in recent_metrics if m.validation_result == result)
                for result in ValidationResult
            },
            "recent_validations": len(recent_metrics),
            "total_validations": len(self.validation_metrics),
        }
