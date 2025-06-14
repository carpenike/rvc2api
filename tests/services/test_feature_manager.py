import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

from backend.services.feature_manager import FeatureManager
from backend.core.services import CoreServices

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# Sample minimal YAML config for testing
SIMPLE_YAML = """
test_feature:
  enabled: true
  core: true
  depends_on: []
  friendly_name: "Test Feature"
"""


def test_load_features_from_yaml(tmp_path):
    """Test loading features from a YAML config file."""
    yaml_path = tmp_path / "features.yaml"
    yaml_path.write_text(SIMPLE_YAML)
    mgr = FeatureManager.from_yaml(str(yaml_path))
    assert "test_feature" in mgr.features
    feat = mgr.features["test_feature"]
    assert feat.enabled is True
    assert feat.core is True
    assert feat.dependencies == []
    assert feat.friendly_name == "Test Feature"


def test_enable_disable_feature(tmp_path):
    """Test enabling and disabling a feature."""
    yaml_path = tmp_path / "features.yaml"
    yaml_path.write_text(SIMPLE_YAML)
    mgr = FeatureManager.from_yaml(str(yaml_path))
    feat = mgr.features["test_feature"]
    feat.enabled = False
    assert not feat.enabled
    feat.enabled = True
    assert feat.enabled


def test_dependency_resolution(tmp_path):
    """Test that dependencies are tracked and can be resolved."""
    yaml = """
base:
  enabled: true
  core: true
  depends_on: []
dependent:
  enabled: true
  core: false
  depends_on: [base]
"""
    yaml_path = tmp_path / "features.yaml"
    yaml_path.write_text(yaml)
    mgr = FeatureManager.from_yaml(str(yaml_path))
    dep = mgr.features["dependent"]
    assert dep.dependencies == ["base"]
    base = mgr.features["base"]
    assert base.enabled


def test_friendly_name_auto_generation(tmp_path):
    """Test that friendly names are auto-generated when not specified."""
    yaml = """
test_feature_name:
  enabled: true
  core: false
  depends_on: []
another_test:
  enabled: true
  core: false
  depends_on: []
  friendly_name: "Custom Name"
"""
    yaml_path = tmp_path / "features.yaml"
    yaml_path.write_text(yaml)
    mgr = FeatureManager.from_yaml(str(yaml_path))

    # Feature without friendly_name should have auto-generated one
    feat1 = mgr.features["test_feature_name"]
    assert feat1.friendly_name == "Test Feature Name"

    # Feature with explicit friendly_name should use that
    feat2 = mgr.features["another_test"]
    assert feat2.friendly_name == "Custom Name"


def test_core_services_injection(tmp_path, mock_core_services):
    """Test that CoreServices can be injected into FeatureManager."""
    yaml_path = tmp_path / "features.yaml"
    yaml_path.write_text(SIMPLE_YAML)
    mgr = FeatureManager.from_yaml(str(yaml_path))

    # Initially should raise since CoreServices not set
    with pytest.raises(RuntimeError, match="Core services not injected"):
        mgr.get_core_services()

    # After injection should work
    mgr.set_core_services(mock_core_services)
    core_services = mgr.get_core_services()
    assert core_services is mock_core_services
    assert hasattr(core_services, 'persistence')
    assert hasattr(core_services, 'database_manager')


def test_feature_manager_with_core_services_integration(tmp_path, mock_core_services):
    """Test FeatureManager integration with CoreServices."""
    yaml = """
feature_needs_persistence:
  enabled: true
  safety_classification: "operational"
  safe_state_action: "continue_operation"
  maintain_state_on_failure: true
  depends_on: []
  description: "Feature that needs database access"
  friendly_name: "Persistence Feature"
"""
    yaml_path = tmp_path / "features.yaml"
    yaml_path.write_text(yaml)
    mgr = FeatureManager.from_yaml(str(yaml_path))

    # Inject CoreServices
    mgr.set_core_services(mock_core_services)

    # Feature should be able to access CoreServices
    assert mgr.get_core_services() is mock_core_services

    # Features can be configured as normal
    feature = mgr.features["feature_needs_persistence"]
    assert feature.enabled is True
    assert feature.dependencies == []


@pytest.mark.asyncio
async def test_feature_manager_startup_with_core_services(tmp_path, mock_core_services):
    """Test FeatureManager startup process with CoreServices injected."""
    yaml_path = tmp_path / "features.yaml"
    yaml_path.write_text(SIMPLE_YAML)
    mgr = FeatureManager.from_yaml(str(yaml_path))

    # Mock the feature's startup method
    feature = mgr.features["test_feature"]
    feature.startup = Mock()
    feature.startup.return_value = None  # Sync method

    # Inject CoreServices before startup
    mgr.set_core_services(mock_core_services)

    # Startup should work
    await mgr.startup()

    # Verify feature startup was called
    feature.startup.assert_called_once()


def test_core_services_access_by_features(tmp_path, mock_core_services):
    """Test that features can access CoreServices through the FeatureManager."""
    yaml_path = tmp_path / "features.yaml"
    yaml_path.write_text(SIMPLE_YAML)
    mgr = FeatureManager.from_yaml(str(yaml_path))
    mgr.set_core_services(mock_core_services)

    # Mock a feature that needs to access CoreServices
    feature = mgr.features["test_feature"]

    # Simulate feature accessing persistence through FeatureManager
    # In real features, they would call get_feature_manager().get_core_services()
    core_services = mgr.get_core_services()
    persistence = core_services.persistence
    database_manager = core_services.database_manager

    assert persistence is not None
    assert database_manager is not None


@pytest.mark.skip(reason="reload_features_from_config is a placeholder and does not update state")
def test_reload_features_from_config(tmp_path):
    """Test reloading features from config does not raise and updates state."""
    yaml_path = tmp_path / "features.yaml"
    yaml_path.write_text(SIMPLE_YAML)
    mgr = FeatureManager.from_yaml(str(yaml_path))
    # Should not raise
    mgr.reload_features_from_config(
        {"test_feature": {"enabled": False, "core": True, "depends_on": []}}
    )
    assert mgr.features["test_feature"].enabled is False


def test_invalid_yaml(tmp_path):
    """Test that invalid YAML raises an error."""
    yaml_path = tmp_path / "bad.yaml"
    yaml_path.write_text("not: [valid: yaml")
    with pytest.raises(Exception):  # noqa: B017
        FeatureManager.from_yaml(str(yaml_path))
