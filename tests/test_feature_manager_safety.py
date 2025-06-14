"""
Comprehensive test suite for Feature Manager safety patterns.

Tests the safety-critical functionality of the feature management system including:
- Dependency resolution and validation
- Safe state transitions
- Health propagation
- Runtime toggling with safety validation
- Recovery workflows
- Safety interlocks and emergency stops
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from backend.services.feature_manager import FeatureManager, get_feature_manager
from backend.services.feature_base import Feature, GenericFeature
from backend.services.feature_models import (
    FeatureConfigurationSet,
    FeatureDefinition,
    FeatureState,
    SafetyClassification,
    SafeStateAction,
    SafetyValidator,
)
from backend.services.safety_service import SafetyService, SafetyInterlock
from backend.core.services import CoreServices


class TestFeature(Feature):
    """Test feature implementation for testing purposes."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.startup_called = False
        self.shutdown_called = False
        self.startup_should_fail = False
        self.health_state = FeatureState.HEALTHY

    async def startup(self) -> None:
        """Test startup implementation."""
        self.startup_called = True
        if self.startup_should_fail:
            raise RuntimeError("Simulated startup failure")
        self.state = FeatureState.HEALTHY

    async def shutdown(self) -> None:
        """Test shutdown implementation."""
        self.shutdown_called = True
        self.state = FeatureState.STOPPED

    async def check_health(self) -> FeatureState:
        """Test health check implementation."""
        return self.health_state


@pytest.fixture
def sample_feature_config():
    """Sample feature configuration for testing (persistence removed - now handled by CoreServices)."""
    return {
        "can_interface": {
            "enabled": True,
            "safety_classification": "critical",
            "safe_state_action": "continue_operation",
            "maintain_state_on_failure": True,
            "depends_on": [],
            "description": "Test CAN interface",
        },
        "firefly": {
            "enabled": True,
            "safety_classification": "position_critical",
            "safe_state_action": "maintain_position",
            "maintain_state_on_failure": True,
            "depends_on": ["can_interface"],
            "description": "Test Firefly RV systems",
        },
        "dashboard": {
            "enabled": True,
            "safety_classification": "operational",
            "safe_state_action": "continue_operation",
            "maintain_state_on_failure": True,
            "depends_on": [],  # persistence dependency removed - now available via CoreServices
            "description": "Test dashboard feature",
        },
        "optional_feature": {
            "enabled": False,
            "safety_classification": "maintenance",
            "safe_state_action": "continue_operation",
            "maintain_state_on_failure": False,
            "depends_on": [],
            "description": "Test optional feature",
        },
    }


@pytest.fixture
def feature_manager(sample_feature_config):
    """Create a test FeatureManager instance."""
    # Create feature definitions
    feature_definitions = {}
    for name, config in sample_feature_config.items():
        config_with_name = {"name": name, **config}
        feature_def = FeatureDefinition(**config_with_name)
        feature_definitions[name] = feature_def

    # Create configuration set
    config_set = FeatureConfigurationSet(features=feature_definitions)

    # Create manager
    manager = FeatureManager(config_set)

    # Register test features
    for name, feature_def in feature_definitions.items():
        feature = TestFeature(
            name=name,
            enabled=feature_def.enabled_by_default,
            core=feature_def.is_safety_critical(),
            config=feature_def.config,
            dependencies=feature_def.dependencies,
            friendly_name=feature_def.friendly_name,
            safety_classification=feature_def.safety_classification,
        )
        manager.register_feature(feature)

    return manager


@pytest.fixture
def safety_feature_manager_with_core_services(sample_feature_config, mock_core_services):
    """Create a test FeatureManager instance with CoreServices injected."""
    # Create feature definitions
    feature_definitions = {}
    for name, config in sample_feature_config.items():
        config_with_name = {"name": name, **config}
        feature_def = FeatureDefinition(**config_with_name)
        feature_definitions[name] = feature_def

    # Create configuration set
    config_set = FeatureConfigurationSet(features=feature_definitions)

    # Create manager
    manager = FeatureManager(config_set)

    # Inject CoreServices
    manager.set_core_services(mock_core_services)

    # Register test features
    for name, feature_def in feature_definitions.items():
        feature = TestFeature(
            name=name,
            enabled=feature_def.enabled_by_default,
            core=feature_def.is_safety_critical(),
            config=feature_def.config,
            dependencies=feature_def.dependencies,
            friendly_name=feature_def.friendly_name,
            safety_classification=feature_def.safety_classification,
        )
        manager.register_feature(feature)

    return manager


class TestDependencyResolution:
    """Test dependency resolution and validation."""

    def test_dependency_resolution_simple(self, feature_manager):
        """Test basic dependency resolution."""
        order = feature_manager._resolve_dependencies()

        # can_interface should come before firefly (its dependent)
        can_interface_idx = order.index("can_interface")
        firefly_idx = order.index("firefly")

        assert can_interface_idx < firefly_idx

        # dashboard has no dependencies now (persistence available via CoreServices)
        assert "dashboard" in order

    def test_circular_dependency_detection(self):
        """Test detection of circular dependencies."""
        config = {
            "feature_a": {
                "enabled": True,
                "safety_classification": "operational",
                "depends_on": ["feature_b"],
                "description": "Test feature A",
            },
            "feature_b": {
                "enabled": True,
                "safety_classification": "operational",
                "depends_on": ["feature_a"],
                "description": "Test feature B",
            },
        }

        feature_definitions = {}
        for name, config_data in config.items():
            config_with_name = {"name": name, **config_data}
            feature_def = FeatureDefinition(**config_with_name)
            feature_definitions[name] = feature_def

        with pytest.raises(ValueError, match="Circular dependency"):
            config_set = FeatureConfigurationSet(features=feature_definitions)
            config_set.validate_dependency_graph()

    def test_missing_dependency_validation(self):
        """Test validation of missing dependencies."""
        config = {
            "feature_a": {
                "enabled": True,
                "safety_classification": "operational",
                "depends_on": ["nonexistent_feature"],
                "description": "Test feature A",
            },
        }

        feature_definitions = {}
        for name, config_data in config.items():
            config_with_name = {"name": name, **config_data}
            feature_def = FeatureDefinition(**config_with_name)
            feature_definitions[name] = feature_def

        with pytest.raises(ValueError, match="depends on 'nonexistent_feature' which does not exist"):
            FeatureConfigurationSet(features=feature_definitions)

    def test_complex_dependency_chain(self):
        """Test complex dependency chain resolution."""
        config = {
            "base": {
                "enabled": True,
                "safety_classification": "critical",
                "depends_on": [],
                "description": "Base feature",
            },
            "layer1_a": {
                "enabled": True,
                "safety_classification": "operational",
                "depends_on": ["base"],
                "description": "Layer 1A feature",
            },
            "layer1_b": {
                "enabled": True,
                "safety_classification": "operational",
                "depends_on": ["base"],
                "description": "Layer 1B feature",
            },
            "layer2": {
                "enabled": True,
                "safety_classification": "operational",
                "depends_on": ["layer1_a", "layer1_b"],
                "description": "Layer 2 feature",
            },
        }

        feature_definitions = {}
        for name, config_data in config.items():
            config_with_name = {"name": name, **config_data}
            feature_def = FeatureDefinition(**config_with_name)
            feature_definitions[name] = feature_def

        config_set = FeatureConfigurationSet(features=feature_definitions)
        order = config_set.get_startup_order()

        # Validate correct ordering
        base_idx = order.index("base")
        layer1_a_idx = order.index("layer1_a")
        layer1_b_idx = order.index("layer1_b")
        layer2_idx = order.index("layer2")

        assert base_idx < layer1_a_idx
        assert base_idx < layer1_b_idx
        assert layer1_a_idx < layer2_idx
        assert layer1_b_idx < layer2_idx


class TestSafeStateTransitions:
    """Test safe state transitions and validation."""

    def test_state_transition_validation(self):
        """Test state transition validation logic."""
        # Test valid transitions
        valid_cases = [
            (FeatureState.STOPPED, FeatureState.INITIALIZING),
            (FeatureState.INITIALIZING, FeatureState.HEALTHY),
            (FeatureState.HEALTHY, FeatureState.DEGRADED),
            (FeatureState.DEGRADED, FeatureState.HEALTHY),
            (FeatureState.FAILED, FeatureState.SAFE_SHUTDOWN),
            (FeatureState.MAINTENANCE, FeatureState.HEALTHY),
        ]

        for from_state, to_state in valid_cases:
            is_valid, _ = SafetyValidator.validate_state_transition(
                from_state, to_state, SafetyClassification.OPERATIONAL
            )
            assert is_valid, f"Should allow transition {from_state} -> {to_state}"

    def test_invalid_state_transitions(self):
        """Test rejection of invalid state transitions."""
        invalid_cases = [
            (FeatureState.STOPPED, FeatureState.HEALTHY),  # Should go through INITIALIZING
            (FeatureState.HEALTHY, FeatureState.STOPPED),  # Should go through shutdown states
            (FeatureState.FAILED, FeatureState.HEALTHY),   # Should go through MAINTENANCE/STOPPED
        ]

        for from_state, to_state in invalid_cases:
            is_valid, reason = SafetyValidator.validate_state_transition(
                from_state, to_state, SafetyClassification.OPERATIONAL
            )
            assert not is_valid, f"Should reject transition {from_state} -> {to_state}: {reason}"

    def test_critical_feature_transition_restrictions(self):
        """Test additional restrictions for critical features."""
        # Critical features should not go directly from HEALTHY to FAILED
        is_valid, reason = SafetyValidator.validate_state_transition(
            FeatureState.HEALTHY,
            FeatureState.FAILED,
            SafetyClassification.CRITICAL
        )
        assert not is_valid
        assert "DEGRADED" in reason

    def test_position_critical_transition_restrictions(self):
        """Test restrictions for position-critical features."""
        # Position-critical features should prefer SAFE_SHUTDOWN over FAILED
        is_valid, reason = SafetyValidator.validate_state_transition(
            FeatureState.HEALTHY,
            FeatureState.FAILED,
            SafetyClassification.POSITION_CRITICAL
        )
        assert not is_valid
        assert "SAFE_SHUTDOWN" in reason

    def test_safe_transition_recommendations(self):
        """Test safe transition recommendations."""
        # Test critical feature needing intermediate state
        safe_state = SafetyValidator.get_safe_transition(
            FeatureState.HEALTHY,
            FeatureState.FAILED,
            SafetyClassification.CRITICAL
        )
        assert safe_state == FeatureState.DEGRADED

        # Test position-critical feature preferring safe shutdown
        safe_state = SafetyValidator.get_safe_transition(
            FeatureState.HEALTHY,
            FeatureState.FAILED,
            SafetyClassification.POSITION_CRITICAL
        )
        assert safe_state == FeatureState.SAFE_SHUTDOWN

    def test_emergency_stop_conditions(self):
        """Test emergency stop detection logic."""
        # Critical feature failure should trigger emergency stop
        assert SafetyValidator.is_emergency_stop_required(
            FeatureState.FAILED,
            SafetyClassification.CRITICAL
        )

        # Position-critical with failed dependencies should trigger emergency stop
        assert SafetyValidator.is_emergency_stop_required(
            FeatureState.DEGRADED,
            SafetyClassification.POSITION_CRITICAL,
            failed_dependencies={"critical_dependency"}
        )

        # Multiple safety-related failures should trigger emergency stop
        assert SafetyValidator.is_emergency_stop_required(
            FeatureState.FAILED,
            SafetyClassification.SAFETY_RELATED,
            failed_dependencies={"dep1", "dep2"}
        )


class TestHealthPropagation:
    """Test health monitoring and propagation."""

    @pytest.mark.asyncio
    async def test_basic_health_propagation(self, feature_manager):
        """Test basic health state propagation."""
        # Get features
        can_interface = feature_manager.get_feature("can_interface")
        firefly = feature_manager.get_feature("firefly")

        # Start with healthy state
        can_interface.state = FeatureState.HEALTHY
        firefly.state = FeatureState.HEALTHY

        # Simulate can_interface failure
        can_interface.state = FeatureState.FAILED

        # Trigger health propagation
        await feature_manager._propagate_health_changes(
            "can_interface", FeatureState.FAILED, FeatureState.HEALTHY
        )

        # Check that firefly was notified and degraded
        assert len(firefly._failed_dependencies) > 0
        assert "can_interface" in firefly._failed_dependencies

    @pytest.mark.asyncio
    async def test_health_recovery_propagation(self, feature_manager):
        """Test health recovery propagation."""
        # Get features
        can_interface = feature_manager.get_feature("can_interface")
        firefly = feature_manager.get_feature("firefly")

        # Start with failed dependency
        can_interface.state = FeatureState.FAILED
        firefly._failed_dependencies.add("can_interface")
        firefly.state = FeatureState.DEGRADED

        # Simulate can_interface recovery
        can_interface.state = FeatureState.HEALTHY

        # Trigger recovery propagation
        await feature_manager._propagate_health_changes(
            "can_interface", FeatureState.HEALTHY, FeatureState.FAILED
        )

        # Check that firefly was notified of recovery
        # Note: The actual recovery logic is in the feature's on_dependency_recovered method

    @pytest.mark.asyncio
    async def test_critical_failure_handling(self, feature_manager):
        """Test handling of critical feature failures."""
        # Get critical feature (can_interface is critical in our test config)
        can_interface = feature_manager.get_feature("can_interface")

        # Simulate critical failure
        can_interface.state = FeatureState.FAILED

        # This should trigger critical failure handling
        await feature_manager._handle_critical_failure("can_interface")

        # Verify safe state procedures were initiated
        # (Implementation would check for safe state entry, logging, etc.)

    @pytest.mark.asyncio
    async def test_system_health_check(self, feature_manager):
        """Test comprehensive system health check."""
        # Set up various health states
        features = feature_manager.get_all_features()

        # Run health check
        health_report = await feature_manager.check_system_health()

        # Verify report structure
        assert "status" in health_report
        assert "features" in health_report
        assert "summary" in health_report
        assert "timestamp" in health_report

        # Verify summary data
        summary = health_report["summary"]
        assert "total_features" in summary
        assert "enabled_features" in summary
        assert "healthy_features" in summary


class TestRuntimeToggling:
    """Test runtime feature toggling with safety validation."""

    @pytest.mark.asyncio
    async def test_safe_feature_toggle(self, feature_manager):
        """Test toggling a safe (non-critical) feature."""
        # Toggle optional feature on
        success, message = await feature_manager.request_feature_toggle(
            "optional_feature", enabled=True, user="test_user", reason="Testing"
        )

        assert success
        assert "successfully enabled" in message

        optional_feature = feature_manager.get_feature("optional_feature")
        assert optional_feature.enabled
        assert optional_feature.startup_called

    @pytest.mark.asyncio
    async def test_safety_critical_toggle_rejection(self, feature_manager):
        """Test rejection of safety-critical feature toggle without override."""
        # Attempt to toggle critical feature without override
        success, message = await feature_manager.request_feature_toggle(
            "can_interface", enabled=False, user="test_user", reason="Testing"
        )

        assert not success
        assert "safety-critical" in message
        assert "override" in message

    @pytest.mark.asyncio
    async def test_safety_override_with_authorization(self, feature_manager):
        """Test safety override with proper authorization."""
        # Toggle critical feature with valid authorization
        success, message = await feature_manager.request_feature_toggle(
            "can_interface",
            enabled=False,
            user="admin",
            reason="Maintenance",
            override_safety=True,
            authorization_code="SAFETY_OVERRIDE_ADMIN"
        )

        assert success
        assert "successfully disabled" in message

    @pytest.mark.asyncio
    async def test_invalid_authorization_rejection(self, feature_manager):
        """Test rejection of invalid authorization codes."""
        # Attempt toggle with invalid authorization
        success, message = await feature_manager.request_feature_toggle(
            "can_interface",
            enabled=False,
            user="admin",
            reason="Maintenance",
            override_safety=True,
            authorization_code="INVALID_CODE"
        )

        assert not success
        assert "Invalid authorization" in message

    @pytest.mark.asyncio
    async def test_dependency_protection(self, feature_manager):
        """Test protection of features with safety-critical dependents."""
        # Try to disable can_interface which has firefly depending on it
        success, message = await feature_manager.request_feature_toggle(
            "can_interface", enabled=False, user="test_user", reason="Testing"
        )

        # Should be rejected due to safety-critical dependent
        assert not success
        assert "dependents" in message.lower()

    @pytest.mark.asyncio
    async def test_position_critical_deployment_check(self, feature_manager):
        """Test position-critical feature deployment checking."""
        # Mock the deployment check to return True
        with patch.object(feature_manager, '_is_device_deployed', return_value=True):
            success, message = await feature_manager.request_feature_toggle(
                "firefly", enabled=False, user="test_user", reason="Testing"
            )

            assert not success
            assert "deployed" in message
            assert "maintain current position" in message


class TestCoreServicesIntegration:
    """Test integration between FeatureManager and CoreServices."""

    def test_core_services_injection_safety(self, safety_feature_manager_with_core_services):
        """Test that CoreServices injection works properly in safety context."""
        manager = safety_feature_manager_with_core_services

        # Should have CoreServices available
        core_services = manager.get_core_services()
        assert core_services is not None
        assert hasattr(core_services, 'persistence')
        assert hasattr(core_services, 'database_manager')

    @pytest.mark.asyncio
    async def test_safety_audit_persistence(self, safety_feature_manager_with_core_services):
        """Test that safety events can be persisted via CoreServices."""
        manager = safety_feature_manager_with_core_services
        core_services = manager.get_core_services()

        # Mock audit logging to persistence
        with patch.object(manager, '_audit_log_feature_action') as mock_audit:
            # Trigger a safety-related action
            await manager.request_feature_toggle(
                "can_interface",
                enabled=False,
                user="test_user",
                reason="Safety test"
            )

            # Verify audit was called (would persist to database via CoreServices)
            mock_audit.assert_called()

    @pytest.mark.asyncio
    async def test_startup_with_core_services(self, safety_feature_manager_with_core_services):
        """Test feature manager startup with CoreServices available."""
        manager = safety_feature_manager_with_core_services

        # Should be able to start up with CoreServices injected
        await manager.startup()

        # Features should have access to persistence through CoreServices
        for feature in manager.features.values():
            if hasattr(feature, 'enabled') and feature.enabled:
                assert feature.startup_called

    def test_legacy_persistence_compatibility(self, safety_feature_manager_with_core_services):
        """Test that removing persistence from features doesn't break safety checks."""
        manager = safety_feature_manager_with_core_services

        # Dashboard feature no longer depends on persistence but should work
        dashboard = manager.get_feature("dashboard")
        assert dashboard is not None
        assert dashboard.dependencies == []  # No more persistence dependency

        # But persistence is still available via CoreServices
        core_services = manager.get_core_services()
        assert core_services.persistence is not None


class TestRecoveryWorkflows:
    """Test feature recovery workflows."""

    @pytest.mark.asyncio
    async def test_single_feature_recovery(self, feature_manager):
        """Test recovery of a single failed feature."""
        # Set feature to failed state
        dashboard = feature_manager.get_feature("dashboard")
        dashboard.state = FeatureState.FAILED
        dashboard.enabled = False

        # Attempt recovery
        success, message = await feature_manager.attempt_feature_recovery(
            "dashboard", user="test_user", reason="Recovery test"
        )

        assert success
        assert "successfully recovered" in message
        assert dashboard.enabled
        assert dashboard.state == FeatureState.HEALTHY

    @pytest.mark.asyncio
    async def test_recovery_with_retries(self, feature_manager):
        """Test recovery with retry logic."""
        # Set feature to fail startup initially
        dashboard = feature_manager.get_feature("dashboard")
        dashboard.state = FeatureState.FAILED
        dashboard.startup_should_fail = True

        # Mock to succeed on second attempt
        original_startup = dashboard.startup
        call_count = 0

        async def mock_startup():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("First attempt fails")
            dashboard.startup_should_fail = False
            await original_startup()

        dashboard.startup = mock_startup

        # Attempt recovery
        success, message = await feature_manager.attempt_feature_recovery(
            "dashboard", user="test_user", max_attempts=3
        )

        assert success
        assert "attempt 2" in message

    @pytest.mark.asyncio
    async def test_bulk_recovery(self, feature_manager):
        """Test bulk recovery of multiple features."""
        # Set multiple features to failed state
        dashboard = feature_manager.get_feature("dashboard")
        optional_feature = feature_manager.get_feature("optional_feature")

        dashboard.state = FeatureState.FAILED
        optional_feature.state = FeatureState.FAILED

        # Attempt bulk recovery
        results = await feature_manager.bulk_feature_recovery(
            user="test_user", reason="Bulk recovery test"
        )

        # Check results
        assert len(results) >= 2
        assert all(success for success, _ in results.values())

    @pytest.mark.asyncio
    async def test_recovery_recommendations(self, feature_manager):
        """Test recovery recommendation generation."""
        # Set features to various failed states
        dashboard = feature_manager.get_feature("dashboard")
        firefly = feature_manager.get_feature("firefly")

        dashboard.state = FeatureState.FAILED
        firefly.state = FeatureState.DEGRADED
        firefly._failed_dependencies.add("can_interface")

        # Get recommendations
        recommendations = await feature_manager.get_recovery_recommendations()

        # Verify recommendations structure
        assert "dashboard" in recommendations
        assert "firefly" in recommendations

        dashboard_rec = recommendations["dashboard"]
        assert "recovery_priority" in dashboard_rec
        assert "can_auto_recover" in dashboard_rec
        assert "recommended_actions" in dashboard_rec

        firefly_rec = recommendations["firefly"]
        assert "failed_dependencies" in firefly_rec
        assert len(firefly_rec["failed_dependencies"]) > 0


class TestSafetyService:
    """Test safety service functionality."""

    @pytest.fixture
    def safety_service(self, feature_manager):
        """Create safety service for testing."""
        return SafetyService(feature_manager, health_check_interval=0.1, watchdog_timeout=1.0)

    def test_safety_interlock_creation(self, safety_service):
        """Test creation and configuration of safety interlocks."""
        # Check that default interlocks were created
        assert len(safety_service._interlocks) > 0
        assert "slide_room_safety" in safety_service._interlocks
        assert "awning_safety" in safety_service._interlocks
        assert "leveling_jack_safety" in safety_service._interlocks

    @pytest.mark.asyncio
    async def test_interlock_condition_evaluation(self, safety_service):
        """Test evaluation of interlock conditions."""
        slide_interlock = safety_service._interlocks["slide_room_safety"]

        # Test with safe conditions
        safe_state = {
            "vehicle_speed": 0.0,
            "parking_brake": True,
            "leveling_jacks_down": True,
            "transmission_gear": "PARK",
        }

        conditions_met, reason = await slide_interlock.check_conditions(safe_state)
        assert conditions_met

        # Test with unsafe conditions
        unsafe_state = {
            "vehicle_speed": 5.0,  # Vehicle moving
            "parking_brake": False,
            "leveling_jacks_down": False,
            "transmission_gear": "DRIVE",
        }

        conditions_met, reason = await slide_interlock.check_conditions(unsafe_state)
        assert not conditions_met
        assert "vehicle_not_moving" in reason

    @pytest.mark.asyncio
    async def test_emergency_stop(self, safety_service):
        """Test emergency stop functionality."""
        # Trigger emergency stop
        await safety_service.emergency_stop("Test emergency stop")

        # Verify emergency stop state
        assert safety_service._emergency_stop_active
        assert safety_service._in_safe_state

        # Check that all interlocks are engaged
        for interlock in safety_service._interlocks.values():
            assert interlock.is_engaged

    @pytest.mark.asyncio
    async def test_emergency_stop_reset(self, safety_service):
        """Test emergency stop reset with authorization."""
        # Activate emergency stop
        await safety_service.emergency_stop("Test")
        assert safety_service._emergency_stop_active

        # Reset with valid authorization
        success = await safety_service.reset_emergency_stop("RESET_EMERGENCY")
        assert success
        assert not safety_service._emergency_stop_active

        # Test invalid authorization
        await safety_service.emergency_stop("Test again")
        success = await safety_service.reset_emergency_stop("INVALID_CODE")
        assert not success
        assert safety_service._emergency_stop_active

    def test_safety_status_reporting(self, safety_service):
        """Test safety status reporting."""
        status = safety_service.get_safety_status()

        # Verify status structure
        assert "in_safe_state" in status
        assert "emergency_stop_active" in status
        assert "interlocks" in status
        assert "system_state" in status
        assert "audit_log_entries" in status

        # Verify interlock status
        for interlock_name, interlock_status in status["interlocks"].items():
            assert "engaged" in interlock_status
            assert "feature" in interlock_status
            assert "conditions" in interlock_status


class TestConfigurationValidation:
    """Test configuration loading and validation."""

    def test_valid_configuration_loading(self, sample_feature_config):
        """Test loading of valid configuration."""
        feature_definitions = {}
        for name, config in sample_feature_config.items():
            config_with_name = {"name": name, **config}
            feature_def = FeatureDefinition(**config_with_name)
            feature_definitions[name] = feature_def

        config_set = FeatureConfigurationSet(features=feature_definitions)
        assert len(config_set.features) == len(sample_feature_config)

    def test_invalid_safety_classification(self):
        """Test rejection of invalid safety classification."""
        config = {
            "test_feature": {
                "enabled": True,
                "safety_classification": "invalid_classification",
                "description": "Test feature",
            }
        }

        with pytest.raises(ValueError):
            FeatureDefinition(**{"name": "test_feature", **config["test_feature"]})

    def test_invalid_feature_name(self):
        """Test rejection of invalid feature names."""
        config = {
            "enabled": True,
            "safety_classification": "operational",
            "description": "Test feature",
        }

        # Test invalid characters
        with pytest.raises(ValueError, match="alphanumeric"):
            FeatureDefinition(name="invalid-name!", **config)

        # Test empty name
        with pytest.raises(ValueError):
            FeatureDefinition(name="", **config)

    def test_safe_state_action_validation(self):
        """Test validation of safe state actions."""
        # Position-critical features should use maintain_position or emergency_stop
        config = {
            "name": "test_position_critical",
            "enabled": True,
            "safety_classification": "position_critical",
            "safe_state_action": "controlled_shutdown",  # Invalid for position-critical
            "description": "Test feature",
        }

        with pytest.raises(ValueError, match="maintain_position or emergency_stop"):
            FeatureDefinition(**config)

    def test_configuration_set_methods(self, sample_feature_config):
        """Test FeatureConfigurationSet utility methods."""
        feature_definitions = {}
        for name, config in sample_feature_config.items():
            config_with_name = {"name": name, **config}
            feature_def = FeatureDefinition(**config_with_name)
            feature_definitions[name] = feature_def

        config_set = FeatureConfigurationSet(features=feature_definitions)

        # Test filtering by classification
        critical_features = config_set.get_features_by_classification(SafetyClassification.CRITICAL)
        assert len(critical_features) > 0
        assert all(f.safety_classification == SafetyClassification.CRITICAL for f in critical_features)

        # Test getting safety-critical features
        safety_critical = config_set.get_critical_features()
        assert len(safety_critical) > 0

        # Test getting toggleable features
        toggleable = config_set.get_toggleable_features()
        assert len(toggleable) > 0


class TestPerformance:
    """Test performance characteristics of the safety system."""

    @pytest.mark.asyncio
    async def test_health_check_performance(self, feature_manager):
        """Test health check performance."""
        import time

        # Measure health check time
        start_time = time.time()
        health_report = await feature_manager.check_system_health()
        duration = time.time() - start_time

        # Health check should complete quickly (< 1 second for test features)
        assert duration < 1.0
        assert health_report["status"] in ["healthy", "degraded", "critical"]

    @pytest.mark.asyncio
    async def test_dependency_resolution_performance(self, feature_manager):
        """Test dependency resolution performance."""
        import time

        # Measure dependency resolution time
        start_time = time.time()
        order = feature_manager._resolve_dependencies()
        duration = time.time() - start_time

        # Dependency resolution should be fast
        assert duration < 0.1
        assert len(order) > 0

    @pytest.mark.asyncio
    async def test_bulk_operations_performance(self, feature_manager):
        """Test performance of bulk operations."""
        import time

        # Set multiple features to failed state
        for feature_name, feature in feature_manager.get_all_features().items():
            if not feature_manager._feature_definitions[feature_name].is_safety_critical():
                feature.state = FeatureState.FAILED

        # Measure bulk recovery time
        start_time = time.time()
        results = await feature_manager.bulk_feature_recovery()
        duration = time.time() - start_time

        # Bulk recovery should complete in reasonable time
        assert duration < 5.0  # Should handle test features quickly
        assert len(results) > 0


if __name__ == "__main__":
    # Run tests when executed directly
    pytest.main([__file__, "-v"])
