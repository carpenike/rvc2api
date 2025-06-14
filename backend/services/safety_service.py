"""
Safety service for RV-C vehicle control systems.

Implements ISO 26262-inspired safety patterns including:
- Safety interlocks for position-critical features
- Emergency stop capabilities
- Watchdog monitoring
- Audit logging for safety-critical operations
"""

import asyncio
import logging
import time
from collections.abc import Callable
from datetime import datetime
from typing import Any

from backend.services.feature_models import (
    FeatureState,
    SafeStateAction,
    SafetyClassification,
    SafetyValidator,
)

logger = logging.getLogger(__name__)


class SafetyInterlock:
    """
    Safety interlock for position-critical features.

    Prevents unsafe operations and enforces safety constraints
    for physical positioning systems like slides, awnings, leveling jacks.
    """

    def __init__(
        self,
        name: str,
        feature_name: str,
        interlock_conditions: list[str],
        safe_state_action: SafeStateAction = SafeStateAction.MAINTAIN_POSITION,
    ):
        """
        Initialize safety interlock.

        Args:
            name: Unique identifier for this interlock
            feature_name: Name of the feature this interlock protects
            interlock_conditions: List of conditions that must be met
            safe_state_action: Action to take when interlock is triggered
        """
        self.name = name
        self.feature_name = feature_name
        self.interlock_conditions = interlock_conditions
        self.safe_state_action = safe_state_action
        self.is_engaged = False
        self.engagement_time: datetime | None = None
        self.engagement_reason = ""

    async def check_conditions(self, system_state: dict[str, Any]) -> tuple[bool, str]:
        """
        Check if interlock conditions are satisfied.

        Args:
            system_state: Current system state information

        Returns:
            Tuple of (conditions_met, reason_if_not_met)
        """
        for condition in self.interlock_conditions:
            if not await self._evaluate_condition(condition, system_state):
                return False, f"Interlock condition not met: {condition}"
        return True, "All conditions satisfied"

    async def _evaluate_condition(self, condition: str, system_state: dict[str, Any]) -> bool:
        """
        Evaluate a single interlock condition.

        Args:
            condition: Condition string to evaluate
            system_state: Current system state

        Returns:
            True if condition is met
        """
        # Parse condition (simplified implementation)
        if condition == "vehicle_not_moving":
            return system_state.get("vehicle_speed", 0) < 0.5  # mph
        if condition == "parking_brake_engaged":
            return system_state.get("parking_brake", False)
        if condition == "leveling_jacks_deployed":
            return system_state.get("leveling_jacks_down", False)
        if condition == "engine_not_running":
            return not system_state.get("engine_running", False)
        if condition == "transmission_in_park":
            return system_state.get("transmission_gear", "") == "PARK"
        if condition == "slide_rooms_retracted":
            return system_state.get("all_slides_retracted", True)
        # Unknown condition - fail safe
        logger.warning("Unknown interlock condition: %s", condition)
        return False

    async def engage(self, reason: str) -> None:
        """
        Engage the safety interlock.

        Args:
            reason: Reason for engaging the interlock
        """
        if not self.is_engaged:
            self.is_engaged = True
            self.engagement_time = datetime.utcnow()
            self.engagement_reason = reason

            logger.warning(
                "Safety interlock '%s' ENGAGED for feature '%s': %s",
                self.name, self.feature_name, reason
            )

    async def disengage(self, reason: str = "Manual override") -> None:
        """
        Disengage the safety interlock.

        Args:
            reason: Reason for disengaging the interlock
        """
        if self.is_engaged:
            duration = (datetime.utcnow() - self.engagement_time).total_seconds()
            self.is_engaged = False
            self.engagement_time = None
            self.engagement_reason = ""

            logger.info(
                "Safety interlock '%s' DISENGAGED for feature '%s' after %.1fs: %s",
                self.name, self.feature_name, duration, reason
            )


class SafetyService:
    """
    Comprehensive safety service for RV-C vehicle control systems.

    Implements ISO 26262-inspired safety patterns including interlocks,
    emergency stop, watchdog monitoring, and audit logging.
    """

    def __init__(
        self,
        feature_manager,
        health_check_interval: float = 5.0,
        watchdog_timeout: float = 15.0,
    ):
        """
        Initialize safety service.

        Args:
            feature_manager: FeatureManager instance to monitor
            health_check_interval: Interval between health checks (seconds)
            watchdog_timeout: Watchdog timeout threshold (seconds)
        """
        self.feature_manager = feature_manager
        self.health_check_interval = health_check_interval
        self.watchdog_timeout = watchdog_timeout

        # Safety state tracking
        self._in_safe_state = False
        self._emergency_stop_active = False
        self._last_watchdog_kick = 0.0
        self._watchdog_task: asyncio.Task | None = None
        self._health_monitor_task: asyncio.Task | None = None

        # Interlocks management
        self._interlocks: dict[str, SafetyInterlock] = {}
        self._system_state: dict[str, Any] = {}

        # Audit logging
        self._audit_log: list[dict[str, Any]] = []
        self._max_audit_entries = 1000

        # Initialize default interlocks
        self._setup_default_interlocks()

    def _setup_default_interlocks(self) -> None:
        """Set up default safety interlocks for common RV systems."""

        # Slide room safety interlocks
        slide_interlocks = [
            "vehicle_not_moving",
            "parking_brake_engaged",
            "leveling_jacks_deployed",
            "transmission_in_park",
        ]

        self.add_interlock(SafetyInterlock(
            name="slide_room_safety",
            feature_name="firefly",  # Firefly controls slide rooms
            interlock_conditions=slide_interlocks,
            safe_state_action=SafeStateAction.MAINTAIN_POSITION,
        ))

        # Awning safety interlocks
        awning_interlocks = [
            "vehicle_not_moving",
            "parking_brake_engaged",
        ]

        self.add_interlock(SafetyInterlock(
            name="awning_safety",
            feature_name="firefly",  # Firefly controls awnings
            interlock_conditions=awning_interlocks,
            safe_state_action=SafeStateAction.MAINTAIN_POSITION,
        ))

        # Leveling jack safety interlocks
        leveling_interlocks = [
            "vehicle_not_moving",
            "parking_brake_engaged",
            "transmission_in_park",
            "engine_not_running",
        ]

        self.add_interlock(SafetyInterlock(
            name="leveling_jack_safety",
            feature_name="spartan_k2",  # Spartan K2 controls leveling
            interlock_conditions=leveling_interlocks,
            safe_state_action=SafeStateAction.MAINTAIN_POSITION,
        ))

    def add_interlock(self, interlock: SafetyInterlock) -> None:
        """
        Add a safety interlock to the system.

        Args:
            interlock: SafetyInterlock instance to add
        """
        self._interlocks[interlock.name] = interlock
        logger.info("Added safety interlock: %s for feature %s",
                   interlock.name, interlock.feature_name)

    def update_system_state(self, state_updates: dict[str, Any]) -> None:
        """
        Update system state information used by interlocks.

        Args:
            state_updates: Dictionary of state updates
        """
        self._system_state.update(state_updates)
        logger.debug("Updated system state: %s", state_updates)

    async def check_safety_interlocks(self) -> dict[str, tuple[bool, str]]:
        """
        Check all safety interlocks and engage/disengage as needed.

        Returns:
            Dictionary mapping interlock names to (satisfied, reason) tuples
        """
        results = {}

        for interlock_name, interlock in self._interlocks.items():
            conditions_met, reason = await interlock.check_conditions(self._system_state)
            results[interlock_name] = (conditions_met, reason)

            if not conditions_met and not interlock.is_engaged:
                await interlock.engage(reason)
                await self._audit_log_event(
                    "interlock_engaged",
                    {
                        "interlock": interlock_name,
                        "feature": interlock.feature_name,
                        "reason": reason,
                    }
                )
            elif conditions_met and interlock.is_engaged:
                await interlock.disengage("Conditions satisfied")
                await self._audit_log_event(
                    "interlock_disengaged",
                    {
                        "interlock": interlock_name,
                        "feature": interlock.feature_name,
                        "reason": "Conditions satisfied",
                    }
                )

        return results

    async def emergency_stop(self, reason: str = "Manual trigger") -> None:
        """
        Trigger emergency stop for all position-critical features.

        Args:
            reason: Reason for emergency stop
        """
        if self._emergency_stop_active:
            logger.warning("Emergency stop already active")
            return

        self._emergency_stop_active = True
        logger.critical("=== EMERGENCY STOP ACTIVATED ===")
        logger.critical("Reason: %s", reason)

        await self._audit_log_event(
            "emergency_stop_activated",
            {"reason": reason, "timestamp": datetime.utcnow().isoformat()}
        )

        try:
            # Get all position-critical features
            position_critical_features = []
            for feature_name, feature in self.feature_manager.features.items():
                if hasattr(feature, "_safety_classification"):
                    if feature._safety_classification == SafetyClassification.POSITION_CRITICAL:
                        position_critical_features.append(feature_name)

            # Set all position-critical features to SAFE_SHUTDOWN
            for feature_name in position_critical_features:
                feature = self.feature_manager.get_feature(feature_name)
                if feature and feature.enabled:
                    logger.critical("Emergency stop: Setting %s to SAFE_SHUTDOWN", feature_name)
                    feature.state = FeatureState.SAFE_SHUTDOWN

            # Engage all safety interlocks
            for interlock in self._interlocks.values():
                if not interlock.is_engaged:
                    await interlock.engage(f"Emergency stop: {reason}")

            # Enter system-wide safe state
            await self._enter_safe_state(f"Emergency stop: {reason}")

            logger.critical("=== EMERGENCY STOP COMPLETED ===")

        except Exception as e:
            logger.critical("Error during emergency stop: %s", e)
            await self._audit_log_event(
                "emergency_stop_error",
                {"error": str(e), "reason": reason}
            )

    async def reset_emergency_stop(self, authorization_code: str = "") -> bool:
        """
        Reset emergency stop after manual authorization.

        Args:
            authorization_code: Authorization code for reset

        Returns:
            True if reset was successful
        """
        if not self._emergency_stop_active:
            logger.info("No emergency stop active to reset")
            return True

        # Simple authorization check (in real implementation, this would be more secure)
        if authorization_code != "RESET_EMERGENCY":
            logger.warning("Invalid authorization code for emergency stop reset")
            return False

        logger.info("Resetting emergency stop with authorization")

        self._emergency_stop_active = False

        await self._audit_log_event(
            "emergency_stop_reset",
            {"authorization_code": authorization_code, "timestamp": datetime.utcnow().isoformat()}
        )

        # Note: Individual features and interlocks must be manually re-enabled
        # This requires explicit operator action to ensure safety

        return True

    async def start_monitoring(self) -> None:
        """Start safety monitoring tasks (watchdog and health checks)."""
        if self._health_monitor_task is None:
            self._health_monitor_task = asyncio.create_task(self._health_monitoring_loop())
            logger.info("Started safety health monitoring")

        if self._watchdog_task is None:
            self._watchdog_task = asyncio.create_task(self._watchdog_loop())
            logger.info("Started safety watchdog monitoring")

        # Initialize watchdog
        self._last_watchdog_kick = time.time()

    async def stop_monitoring(self) -> None:
        """Stop safety monitoring tasks."""
        if self._health_monitor_task:
            self._health_monitor_task.cancel()
            try:
                await self._health_monitor_task
            except asyncio.CancelledError:
                pass
            self._health_monitor_task = None
            logger.info("Stopped safety health monitoring")

        if self._watchdog_task:
            self._watchdog_task.cancel()
            try:
                await self._watchdog_task
            except asyncio.CancelledError:
                pass
            self._watchdog_task = None
            logger.info("Stopped safety watchdog monitoring")

    async def _health_monitoring_loop(self) -> None:
        """ISO 26262-compliant health monitoring loop with watchdog pattern."""
        logger.info("Starting safety health monitoring loop")

        while not self._in_safe_state:
            try:
                start_time = time.time()

                # Check feature health via feature manager
                health_report = await self.feature_manager.check_system_health()

                # Check safety interlocks
                interlock_results = await self.check_safety_interlocks()

                # Update watchdog timer
                self._last_watchdog_kick = time.time()

                # Check for emergency conditions
                await self._check_emergency_conditions(health_report, interlock_results)

                # Check monitoring loop performance
                loop_duration = time.time() - start_time
                if loop_duration > self.health_check_interval:
                    logger.warning("Safety monitoring loop took %.2fs (threshold: %.2fs)",
                                 loop_duration, self.health_check_interval)

                await asyncio.sleep(self.health_check_interval)

            except Exception as e:
                logger.critical("Safety monitoring loop failed: %s", e)
                await self._enter_safe_state(f"Monitoring loop failure: {e}")
                break

    async def _watchdog_loop(self) -> None:
        """Separate watchdog task to monitor health check kicks."""
        logger.info("Starting safety watchdog loop")

        while not self._in_safe_state:
            current_time = time.time()
            time_since_kick = current_time - self._last_watchdog_kick

            if time_since_kick > self.watchdog_timeout:
                logger.critical("Safety watchdog timeout detected (%.1fs > %.1fs)",
                              time_since_kick, self.watchdog_timeout)
                await self._enter_safe_state("Watchdog timeout")
                break

            await asyncio.sleep(1.0)

    async def _check_emergency_conditions(
        self,
        health_report: dict[str, Any],
        interlock_results: dict[str, tuple[bool, str]]
    ) -> None:
        """
        Check for conditions that require emergency stop.

        Args:
            health_report: System health report from feature manager
            interlock_results: Results from safety interlock checks
        """
        # Check for critical feature failures
        failed_critical = health_report.get("failed_critical", [])
        if failed_critical:
            logger.critical("Critical features failed: %s", failed_critical)
            await self.emergency_stop(f"Critical feature failure: {', '.join(failed_critical)}")

        # Check for multiple interlock violations
        violated_interlocks = [
            name for name, (satisfied, _) in interlock_results.items()
            if not satisfied
        ]

        if len(violated_interlocks) >= 3:  # Multiple safety violations
            logger.critical("Multiple safety interlocks violated: %s", violated_interlocks)
            await self.emergency_stop(f"Multiple interlock violations: {', '.join(violated_interlocks)}")

    async def _enter_safe_state(self, reason: str) -> None:
        """
        Enter system-wide safe state.

        Args:
            reason: Reason for entering safe state
        """
        if self._in_safe_state:
            return  # Already in safe state

        self._in_safe_state = True
        logger.critical("=== ENTERING SAFE STATE ===")
        logger.critical("Reason: %s", reason)

        await self._audit_log_event(
            "safe_state_entered",
            {"reason": reason, "timestamp": datetime.utcnow().isoformat()}
        )

        try:
            # Capture current device states for forensics
            system_snapshot = dict(self._system_state)
            logger.info("System state snapshot: %s", system_snapshot)

            # Set all safety-critical features to safe shutdown
            await self._shutdown_safety_critical_features()

            # Engage all safety interlocks
            for interlock in self._interlocks.values():
                if not interlock.is_engaged:
                    await interlock.engage(f"Safe state: {reason}")

            logger.critical("=== SAFE STATE ESTABLISHED ===")

        except Exception as e:
            logger.critical("Failed to enter safe state: %s", e)
            await self._audit_log_event(
                "safe_state_error",
                {"error": str(e), "reason": reason}
            )

    async def _shutdown_safety_critical_features(self) -> None:
        """Shut down safety-critical features in controlled manner."""
        for feature_name, feature in self.feature_manager.features.items():
            if hasattr(feature, "_safety_classification"):
                classification = feature._safety_classification

                if classification in [SafetyClassification.CRITICAL, SafetyClassification.POSITION_CRITICAL]:
                    if feature.enabled and feature.state != FeatureState.SAFE_SHUTDOWN:
                        logger.warning("Safe state: Setting %s to SAFE_SHUTDOWN", feature_name)
                        feature.state = FeatureState.SAFE_SHUTDOWN

    async def _audit_log_event(self, event_type: str, details: dict[str, Any]) -> None:
        """
        Log safety-critical event to audit trail.

        Args:
            event_type: Type of event
            details: Event details
        """
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "details": details,
        }

        self._audit_log.append(audit_entry)

        # Trim audit log if it gets too large
        if len(self._audit_log) > self._max_audit_entries:
            self._audit_log = self._audit_log[-self._max_audit_entries:]

        # Log to standard logger as well
        logger.info("AUDIT: %s - %s", event_type, details)

    def get_audit_log(self, max_entries: int = 100) -> list[dict[str, Any]]:
        """
        Get recent audit log entries.

        Args:
            max_entries: Maximum number of entries to return

        Returns:
            List of audit log entries
        """
        return self._audit_log[-max_entries:] if self._audit_log else []

    def get_safety_status(self) -> dict[str, Any]:
        """
        Get comprehensive safety system status.

        Returns:
            Dictionary containing safety system status
        """
        return {
            "in_safe_state": self._in_safe_state,
            "emergency_stop_active": self._emergency_stop_active,
            "watchdog_timeout": self.watchdog_timeout,
            "time_since_last_kick": time.time() - self._last_watchdog_kick,
            "interlocks": {
                name: {
                    "engaged": interlock.is_engaged,
                    "feature": interlock.feature_name,
                    "conditions": interlock.interlock_conditions,
                    "engagement_time": interlock.engagement_time.isoformat() if interlock.engagement_time else None,
                    "engagement_reason": interlock.engagement_reason,
                }
                for name, interlock in self._interlocks.items()
            },
            "system_state": dict(self._system_state),
            "audit_log_entries": len(self._audit_log),
        }
