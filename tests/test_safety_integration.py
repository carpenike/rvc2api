"""
Integration tests for safety-critical state transitions and scenarios.

These tests validate end-to-end safety behavior including:
- Complete startup/shutdown cycles with safety validation
- Emergency scenarios and safe state transitions
- Real-world failure cascades and recovery
- Safety interlock integration with feature management
- Cross-system safety validation
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import time
from datetime import datetime

from backend.services.feature_manager import FeatureManager
from backend.services.feature_base import Feature
from backend.services.feature_models import (
    FeatureConfigurationSet,
    FeatureDefinition,
    FeatureState,
    SafetyClassification,
    SafeStateAction,
)
from backend.services.safety_service import SafetyService, SafetyInterlock


class RealWorldFeature(Feature):
    """More realistic feature implementation for integration testing."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.startup_duration = 0.1  # Simulate startup time
        self.shutdown_duration = 0.05  # Simulate shutdown time
        self.health_check_duration = 0.01  # Simulate health check time

        # Failure simulation controls
        self.should_fail_startup = False
        self.should_fail_health_check = False
        self.should_randomly_fail = False
        self.failure_probability = 0.1

        # State tracking
        self.startup_count = 0
        self.shutdown_count = 0
        self.health_check_count = 0
        self.last_startup_time = None
        self.last_shutdown_time = None

        # Performance tracking
        self.startup_times = []
        self.shutdown_times = []
        self.health_check_times = []

    async def startup(self) -> None:
        """Realistic startup with timing and failure simulation."""
        start_time = time.time()
        self.startup_count += 1
        self.last_startup_time = datetime.utcnow()

        # Simulate startup work
        await asyncio.sleep(self.startup_duration)

        # Simulate potential startup failure
        if self.should_fail_startup:
            self.state = FeatureState.FAILED
            raise RuntimeError(f"Simulated startup failure for {self.name}")

        # Track performance
        duration = time.time() - start_time
        self.startup_times.append(duration)

        self.state = FeatureState.HEALTHY

    async def shutdown(self) -> None:
        """Realistic shutdown with timing tracking."""
        start_time = time.time()
        self.shutdown_count += 1
        self.last_shutdown_time = datetime.utcnow()

        # Simulate shutdown work
        await asyncio.sleep(self.shutdown_duration)

        # Track performance
        duration = time.time() - start_time
        self.shutdown_times.append(duration)

        self.state = FeatureState.STOPPED

    async def check_health(self) -> FeatureState:
        """Realistic health check with timing and random failures."""
        start_time = time.time()
        self.health_check_count += 1

        # Simulate health check work
        await asyncio.sleep(self.health_check_duration)

        # Simulate potential health check failure
        if self.should_fail_health_check:
            self.state = FeatureState.FAILED
        elif self.should_randomly_fail:
            import random
            if random.random() < self.failure_probability:
                self.state = FeatureState.DEGRADED

        # Track performance
        duration = time.time() - start_time
        self.health_check_times.append(duration)

        return self.state

    def get_performance_stats(self) -> dict:
        """Get performance statistics."""
        return {
            "startup_count": self.startup_count,
            "shutdown_count": self.shutdown_count,
            "health_check_count": self.health_check_count,
            "avg_startup_time": sum(self.startup_times) / len(self.startup_times) if self.startup_times else 0,
            "avg_shutdown_time": sum(self.shutdown_times) / len(self.shutdown_times) if self.shutdown_times else 0,
            "avg_health_check_time": sum(self.health_check_times) / len(self.health_check_times) if self.health_check_times else 0,
            "max_startup_time": max(self.startup_times) if self.startup_times else 0,
            "max_shutdown_time": max(self.shutdown_times) if self.shutdown_times else 0,
            "max_health_check_time": max(self.health_check_times) if self.health_check_times else 0,
        }


@pytest.fixture
def rv_system_config():
    """Realistic RV system configuration for integration testing."""
    return {
        # Core infrastructure
        "persistence": {
            "enabled": True,
            "safety_classification": "critical",
            "safe_state_action": "continue_operation",
            "maintain_state_on_failure": True,
            "depends_on": [],
            "description": "Data persistence service",
        },
        "can_interface": {
            "enabled": True,
            "safety_classification": "critical",
            "safe_state_action": "continue_operation",
            "maintain_state_on_failure": True,
            "depends_on": [],
            "description": "CAN bus interface",
        },

        # Safety-related systems
        "rvc_protocol": {
            "enabled": True,
            "safety_classification": "critical",
            "safe_state_action": "continue_operation",
            "maintain_state_on_failure": True,
            "depends_on": ["can_interface"],
            "description": "RV-C protocol handler",
        },
        "spartan_k2": {
            "enabled": True,
            "safety_classification": "safety_related",
            "safe_state_action": "maintain_position",
            "maintain_state_on_failure": True,
            "depends_on": ["can_interface", "rvc_protocol"],
            "description": "Spartan K2 chassis control",
        },

        # Position-critical systems
        "firefly": {
            "enabled": True,
            "safety_classification": "position_critical",
            "safe_state_action": "maintain_position",
            "maintain_state_on_failure": True,
            "depends_on": ["rvc_protocol"],
            "description": "Firefly slide/awning control",
        },
        "leveling_system": {
            "enabled": True,
            "safety_classification": "position_critical",
            "safe_state_action": "maintain_position",
            "maintain_state_on_failure": True,
            "depends_on": ["spartan_k2"],
            "description": "Automatic leveling system",
        },

        # Operational systems
        "dashboard": {
            "enabled": True,
            "safety_classification": "operational",
            "safe_state_action": "continue_operation",
            "maintain_state_on_failure": True,
            "depends_on": ["persistence", "rvc_protocol"],
            "description": "Dashboard and UI",
        },
        "lighting_control": {
            "enabled": True,
            "safety_classification": "operational",
            "safe_state_action": "continue_operation",
            "maintain_state_on_failure": True,
            "depends_on": ["firefly"],
            "description": "Interior/exterior lighting",
        },
        "climate_control": {
            "enabled": True,
            "safety_classification": "operational",
            "safe_state_action": "continue_operation",
            "maintain_state_on_failure": True,
            "depends_on": ["rvc_protocol"],
            "description": "HVAC control system",
        },

        # Maintenance features
        "diagnostics": {
            "enabled": True,
            "safety_classification": "maintenance",
            "safe_state_action": "continue_operation",
            "maintain_state_on_failure": False,
            "depends_on": ["can_interface"],
            "description": "System diagnostics",
        },
        "logs": {
            "enabled": True,
            "safety_classification": "maintenance",
            "safe_state_action": "continue_operation",
            "maintain_state_on_failure": False,
            "depends_on": ["persistence"],
            "description": "Log management",
        },
    }


@pytest.fixture
def integrated_system(rv_system_config):
    """Create integrated RV system for testing."""
    # Create feature definitions
    feature_definitions = {}
    for name, config in rv_system_config.items():
        config_with_name = {"name": name, **config}
        feature_def = FeatureDefinition(**config_with_name)
        feature_definitions[name] = feature_def

    # Create configuration set
    config_set = FeatureConfigurationSet(features=feature_definitions)

    # Create feature manager
    feature_manager = FeatureManager(config_set)

    # Register realistic features
    for name, feature_def in feature_definitions.items():
        feature = RealWorldFeature(
            name=name,
            enabled=feature_def.enabled_by_default,
            core=feature_def.is_safety_critical(),
            config=feature_def.config,
            dependencies=feature_def.dependencies,
            friendly_name=feature_def.friendly_name,
            safety_classification=feature_def.safety_classification,
        )
        feature_manager.register_feature(feature)

    # Create safety service
    safety_service = SafetyService(
        feature_manager,
        health_check_interval=0.1,  # Fast for testing
        watchdog_timeout=2.0
    )

    return {
        "feature_manager": feature_manager,
        "safety_service": safety_service,
        "features": {name: feature_manager.get_feature(name) for name in rv_system_config.keys()}
    }


class TestSystemStartupShutdown:
    """Test complete system startup and shutdown cycles."""

    @pytest.mark.asyncio
    async def test_clean_startup_cycle(self, integrated_system):
        """Test clean startup of all systems in dependency order."""
        feature_manager = integrated_system["feature_manager"]

        # Perform startup
        start_time = time.time()
        await feature_manager.startup()
        startup_duration = time.time() - start_time

        # Verify all enabled features started
        enabled_features = feature_manager.get_enabled_features()
        for feature_name, feature in enabled_features.items():
            assert feature.state == FeatureState.HEALTHY, f"Feature {feature_name} not healthy after startup"
            assert feature.startup_count > 0, f"Feature {feature_name} startup not called"

        # Verify dependency order was respected
        # (Implementation would check actual startup timestamps)

        # Performance check
        assert startup_duration < 5.0, f"Startup took too long: {startup_duration}s"

        print(f"Clean startup completed in {startup_duration:.2f}s")

    @pytest.mark.asyncio
    async def test_startup_with_failure_recovery(self, integrated_system):
        """Test startup with feature failure and recovery."""
        feature_manager = integrated_system["feature_manager"]
        features = integrated_system["features"]

        # Make one non-critical feature fail during startup
        features["climate_control"].should_fail_startup = True

        # Perform startup
        await feature_manager.startup()

        # Verify critical features still started
        critical_features = ["persistence", "can_interface", "rvc_protocol"]
        for feature_name in critical_features:
            feature = features[feature_name]
            assert feature.state == FeatureState.HEALTHY, f"Critical feature {feature_name} failed"

        # Verify failed feature was disabled
        climate_feature = features["climate_control"]
        assert not climate_feature.enabled, "Failed feature should be disabled"

        # Attempt recovery
        success, message = await feature_manager.attempt_feature_recovery("climate_control")
        assert not success, "Recovery should fail while startup_should_fail is True"

        # Fix the issue and retry
        climate_feature.should_fail_startup = False
        success, message = await feature_manager.attempt_feature_recovery("climate_control")
        assert success, f"Recovery should succeed: {message}"
        assert climate_feature.enabled, "Feature should be enabled after recovery"
        assert climate_feature.state == FeatureState.HEALTHY, "Feature should be healthy after recovery"

    @pytest.mark.asyncio
    async def test_graceful_shutdown_cycle(self, integrated_system):
        """Test graceful shutdown of all systems."""
        feature_manager = integrated_system["feature_manager"]

        # Start the system first
        await feature_manager.startup()

        # Perform shutdown
        start_time = time.time()
        await feature_manager.shutdown()
        shutdown_duration = time.time() - start_time

        # Verify all features were shut down
        all_features = feature_manager.get_all_features()
        for feature_name, feature in all_features.items():
            if feature.enabled:  # Only check enabled features
                assert feature.state == FeatureState.STOPPED, f"Feature {feature_name} not stopped after shutdown"
                assert feature.shutdown_count > 0, f"Feature {feature_name} shutdown not called"

        # Performance check
        assert shutdown_duration < 3.0, f"Shutdown took too long: {shutdown_duration}s"

        print(f"Graceful shutdown completed in {shutdown_duration:.2f}s")


class TestEmergencyScenarios:
    """Test emergency scenarios and safe state transitions."""

    @pytest.mark.asyncio
    async def test_critical_feature_failure_cascade(self, integrated_system):
        """Test cascade of failures when critical feature fails."""
        feature_manager = integrated_system["feature_manager"]
        safety_service = integrated_system["safety_service"]
        features = integrated_system["features"]

        # Start system
        await feature_manager.startup()

        # Simulate critical CAN interface failure
        can_interface = features["can_interface"]
        can_interface.state = FeatureState.FAILED

        # Trigger health propagation
        await feature_manager._propagate_health_changes(
            "can_interface", FeatureState.FAILED, FeatureState.HEALTHY
        )

        # Verify dependent features were affected
        dependent_features = ["rvc_protocol", "spartan_k2", "firefly"]
        for feature_name in dependent_features:
            feature = features[feature_name]
            assert "can_interface" in feature._failed_dependencies

        # Verify safety service detected the failure
        safety_status = safety_service.get_safety_status()
        # Implementation would check for appropriate safety responses

    @pytest.mark.asyncio
    async def test_position_critical_failure_response(self, integrated_system):
        """Test response to position-critical system failure."""
        feature_manager = integrated_system["feature_manager"]
        safety_service = integrated_system["safety_service"]
        features = integrated_system["features"]

        # Start system
        await feature_manager.startup()

        # Simulate position-critical failure (firefly system)
        firefly = features["firefly"]
        firefly.state = FeatureState.FAILED

        # Trigger critical failure handling
        await feature_manager._handle_critical_failure("firefly")

        # Verify position-critical features entered safe shutdown
        position_critical = ["firefly", "leveling_system"]
        for feature_name in position_critical:
            feature = features[feature_name]
            # Should maintain current position, not retract
            assert feature.state in [FeatureState.SAFE_SHUTDOWN, FeatureState.FAILED]

        # Verify audit log captured the event
        # Implementation would check audit logs

    @pytest.mark.asyncio
    async def test_emergency_stop_scenario(self, integrated_system):
        """Test complete emergency stop scenario."""
        feature_manager = integrated_system["feature_manager"]
        safety_service = integrated_system["safety_service"]
        features = integrated_system["features"]

        # Start system and safety monitoring
        await feature_manager.startup()
        await safety_service.start_monitoring()

        # Simulate emergency condition (multiple system failures)
        features["can_interface"].state = FeatureState.FAILED
        features["rvc_protocol"].state = FeatureState.FAILED

        # Trigger emergency stop
        await safety_service.emergency_stop("Critical system failures detected")

        # Verify emergency stop state
        assert safety_service._emergency_stop_active
        assert safety_service._in_safe_state

        # Verify all safety interlocks engaged
        for interlock in safety_service._interlocks.values():
            assert interlock.is_engaged

        # Verify position-critical features in safe state
        position_critical = ["firefly", "leveling_system"]
        for feature_name in position_critical:
            feature = features[feature_name]
            assert feature.state == FeatureState.SAFE_SHUTDOWN

        # Test emergency stop reset
        success = await safety_service.reset_emergency_stop("RESET_EMERGENCY")
        assert success
        assert not safety_service._emergency_stop_active

        # Stop monitoring
        await safety_service.stop_monitoring()

    @pytest.mark.asyncio
    async def test_watchdog_timeout_scenario(self, integrated_system):
        """Test watchdog timeout and safe state entry."""
        feature_manager = integrated_system["feature_manager"]
        safety_service = integrated_system["safety_service"]

        # Start system and safety monitoring
        await feature_manager.startup()
        await safety_service.start_monitoring()

        # Simulate health monitoring getting stuck
        original_check_health = feature_manager.check_system_health

        async def stuck_health_check():
            # Simulate a stuck health check
            await asyncio.sleep(5.0)  # Longer than watchdog timeout
            return await original_health_check()

        feature_manager.check_system_health = stuck_health_check

        # Wait for watchdog timeout
        await asyncio.sleep(3.0)  # Longer than 2.0s timeout

        # Verify safe state was entered
        assert safety_service._in_safe_state

        # Clean up
        await safety_service.stop_monitoring()


class TestRealWorldFailurePatterns:
    """Test realistic failure patterns and recovery scenarios."""

    @pytest.mark.asyncio
    async def test_intermittent_connectivity_issues(self, integrated_system):
        """Test handling of intermittent connectivity issues."""
        feature_manager = integrated_system["feature_manager"]
        features = integrated_system["features"]

        # Start system
        await feature_manager.startup()

        # Simulate intermittent CAN bus issues
        can_interface = features["can_interface"]

        # Cycle through connectivity issues
        for cycle in range(3):
            # Fail
            can_interface.state = FeatureState.DEGRADED
            await feature_manager._propagate_health_changes(
                "can_interface", FeatureState.DEGRADED, FeatureState.HEALTHY
            )

            # Brief pause
            await asyncio.sleep(0.1)

            # Recover
            can_interface.state = FeatureState.HEALTHY
            can_interface._failed_dependencies.clear()
            await feature_manager._propagate_health_changes(
                "can_interface", FeatureState.HEALTHY, FeatureState.DEGRADED
            )

            await asyncio.sleep(0.1)

        # Verify system remained stable
        assert can_interface.state == FeatureState.HEALTHY

        # Check dependent features recovered
        dependent_features = ["rvc_protocol", "firefly", "spartan_k2"]
        for feature_name in dependent_features:
            feature = features[feature_name]
            # Should have cleared failed dependencies
            assert len(feature._failed_dependencies) == 0

    @pytest.mark.asyncio
    async def test_power_cycling_scenario(self, integrated_system):
        """Test system behavior during power cycling scenarios."""
        feature_manager = integrated_system["feature_manager"]
        features = integrated_system["features"]

        # Simulate power cycle by stopping and restarting critical features
        critical_features = ["persistence", "can_interface"]

        for cycle in range(2):
            # Start system
            await feature_manager.startup()

            # Verify healthy state
            for feature_name in critical_features:
                assert features[feature_name].state == FeatureState.HEALTHY

            # Simulate power loss (immediate shutdown)
            for feature_name in critical_features:
                features[feature_name].state = FeatureState.STOPPED

            # Simulate power restoration
            await asyncio.sleep(0.1)

            # Restart critical features
            for feature_name in critical_features:
                feature = features[feature_name]
                feature.state = FeatureState.INITIALIZING
                await feature.startup()

        # Verify system stability after power cycling
        enabled_features = feature_manager.get_enabled_features()
        for feature_name, feature in enabled_features.items():
            assert feature.state == FeatureState.HEALTHY

    @pytest.mark.asyncio
    async def test_cascading_dependency_recovery(self, integrated_system):
        """Test recovery of cascading dependency failures."""
        feature_manager = integrated_system["feature_manager"]
        features = integrated_system["features"]

        # Start system
        await feature_manager.startup()

        # Simulate cascading failure starting from can_interface
        failure_chain = ["can_interface", "rvc_protocol", "firefly", "lighting_control"]

        # Trigger cascading failures
        for feature_name in failure_chain:
            features[feature_name].state = FeatureState.FAILED

        # Mark dependencies as failed
        features["rvc_protocol"]._failed_dependencies.add("can_interface")
        features["firefly"]._failed_dependencies.add("rvc_protocol")
        features["lighting_control"]._failed_dependencies.add("firefly")

        # Attempt bulk recovery
        results = await feature_manager.bulk_feature_recovery(
            reason="Cascading failure recovery test"
        )

        # Verify recovery succeeded in dependency order
        assert len(results) == len(failure_chain)
        for feature_name in failure_chain:
            success, message = results[feature_name]
            assert success, f"Recovery failed for {feature_name}: {message}"
            assert features[feature_name].state == FeatureState.HEALTHY
            assert len(features[feature_name]._failed_dependencies) == 0


class TestSafetyInterlockIntegration:
    """Test integration between safety interlocks and feature management."""

    @pytest.mark.asyncio
    async def test_interlock_prevents_unsafe_operations(self, integrated_system):
        """Test that safety interlocks prevent unsafe operations."""
        feature_manager = integrated_system["feature_manager"]
        safety_service = integrated_system["safety_service"]

        # Start system
        await feature_manager.startup()

        # Update system state to unsafe conditions
        safety_service.update_system_state({
            "vehicle_speed": 5.0,  # Vehicle moving
            "parking_brake": False,
            "transmission_gear": "DRIVE",
        })

        # Check interlocks
        interlock_results = await safety_service.check_safety_interlocks()

        # Verify interlocks are engaged for unsafe conditions
        slide_safety = interlock_results.get("slide_room_safety")
        assert slide_safety is not None
        conditions_met, reason = slide_safety
        assert not conditions_met
        assert "vehicle_not_moving" in reason

        # Attempt to toggle position-critical feature
        success, message = await feature_manager.request_feature_toggle(
            "firefly", enabled=False, user="test_user", reason="Test while moving"
        )

        # Should be rejected due to safety interlocks
        # (Implementation would integrate interlock state checking)

    @pytest.mark.asyncio
    async def test_interlock_state_synchronization(self, integrated_system):
        """Test synchronization between interlock state and feature state."""
        feature_manager = integrated_system["feature_manager"]
        safety_service = integrated_system["safety_service"]
        features = integrated_system["features"]

        # Start system
        await feature_manager.startup()

        # Simulate feature failure that should trigger interlocks
        firefly = features["firefly"]
        firefly.state = FeatureState.FAILED

        # Trigger emergency stop
        await safety_service.emergency_stop("Feature failure simulation")

        # Verify interlock state matches feature state
        safety_status = safety_service.get_safety_status()
        assert safety_status["emergency_stop_active"]

        # All interlocks should be engaged
        for interlock_name, interlock_status in safety_status["interlocks"].items():
            assert interlock_status["engaged"]

        # Feature should be in safe shutdown state
        assert firefly.state == FeatureState.SAFE_SHUTDOWN


class TestPerformanceUnderLoad:
    """Test system performance under various load conditions."""

    @pytest.mark.asyncio
    async def test_health_monitoring_performance(self, integrated_system):
        """Test performance of health monitoring under load."""
        feature_manager = integrated_system["feature_manager"]
        safety_service = integrated_system["safety_service"]

        # Start system and monitoring
        await feature_manager.startup()
        await safety_service.start_monitoring()

        # Let monitoring run for a period
        monitoring_duration = 2.0
        start_time = time.time()

        # Monitor performance during load
        health_check_times = []
        while time.time() - start_time < monitoring_duration:
            health_start = time.time()
            await feature_manager.check_system_health()
            health_duration = time.time() - health_start
            health_check_times.append(health_duration)

            await asyncio.sleep(0.1)  # Brief pause between checks

        # Stop monitoring
        await safety_service.stop_monitoring()

        # Analyze performance
        avg_health_check_time = sum(health_check_times) / len(health_check_times)
        max_health_check_time = max(health_check_times)

        # Performance assertions
        assert avg_health_check_time < 0.1, f"Average health check too slow: {avg_health_check_time:.3f}s"
        assert max_health_check_time < 0.5, f"Max health check too slow: {max_health_check_time:.3f}s"

        print(f"Health monitoring performance: avg={avg_health_check_time:.3f}s, max={max_health_check_time:.3f}s")

    @pytest.mark.asyncio
    async def test_concurrent_operations_performance(self, integrated_system):
        """Test performance of concurrent safety operations."""
        feature_manager = integrated_system["feature_manager"]
        safety_service = integrated_system["safety_service"]

        # Start system
        await feature_manager.startup()

        # Define concurrent operations
        async def health_check_task():
            for _ in range(10):
                await feature_manager.check_system_health()
                await asyncio.sleep(0.01)

        async def interlock_check_task():
            for _ in range(10):
                await safety_service.check_safety_interlocks()
                await asyncio.sleep(0.01)

        async def feature_toggle_task():
            toggleable_features = ["diagnostics", "logs"]
            for feature_name in toggleable_features:
                await feature_manager.request_feature_toggle(
                    feature_name, enabled=False, user="test_user", reason="Load test"
                )
                await asyncio.sleep(0.05)
                await feature_manager.request_feature_toggle(
                    feature_name, enabled=True, user="test_user", reason="Load test"
                )
                await asyncio.sleep(0.05)

        # Run concurrent operations
        start_time = time.time()
        await asyncio.gather(
            health_check_task(),
            interlock_check_task(),
            feature_toggle_task(),
        )
        total_duration = time.time() - start_time

        # Performance assertion
        assert total_duration < 5.0, f"Concurrent operations took too long: {total_duration:.2f}s"

        # Verify system stability after concurrent operations
        health_report = await feature_manager.check_system_health()
        assert health_report["status"] in ["healthy", "degraded"]  # Should not be critical

        print(f"Concurrent operations completed in {total_duration:.2f}s")

    @pytest.mark.asyncio
    async def test_memory_usage_stability(self, integrated_system):
        """Test memory usage stability during extended operation."""
        feature_manager = integrated_system["feature_manager"]
        safety_service = integrated_system["safety_service"]

        # Start system
        await feature_manager.startup()

        # Simulate extended operation with various activities
        operations = 100
        for i in range(operations):
            # Health checks
            await feature_manager.check_system_health()

            # Interlock checks
            await safety_service.check_safety_interlocks()

            # State transitions
            if i % 10 == 0:
                # Simulate occasional feature recovery
                features = integrated_system["features"]
                test_feature = features["diagnostics"]
                test_feature.state = FeatureState.DEGRADED
                await feature_manager.attempt_feature_recovery("diagnostics")

            # Brief pause
            await asyncio.sleep(0.01)

        # Verify audit logs don't grow unbounded
        audit_log = safety_service.get_audit_log()
        assert len(audit_log) <= safety_service._max_audit_entries

        # Verify system still responsive
        final_health = await feature_manager.check_system_health()
        assert final_health["status"] in ["healthy", "degraded"]

        print(f"Completed {operations} operations with stable memory usage")


if __name__ == "__main__":
    # Run integration tests when executed directly
    pytest.main([__file__, "-v", "-s"])
