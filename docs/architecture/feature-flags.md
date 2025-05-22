# Feature Flag System

## Overview

The rvc2api backend uses a robust, production-ready feature flag system to manage optional and experimental features. This system is designed for maintainability, extensibility, and runtime configurability.

## How Feature Flags Work

- **Definition**: All available (registerable) features are defined in `backend/services/feature_flags.yaml`. This YAML file specifies:
  - The feature name
  - Default enabled/disabled state
  - Whether the feature is core/required
  - Any dependencies on other features

- **Registration**: At startup, the backend loads all features from `feature_flags.yaml` and registers them with the `FeatureManager`.

- **Runtime State**: The actual enabled/disabled state of each feature is determined at runtime by environment variables, Pydantic settings, or other config sources. This allows you to override the YAML defaults without editing the file.
  - For example, setting `ENABLE_CANBUS=false` in your environment or config will disable the `canbus` feature, even if it is enabled by default in YAML.

- **Dependencies**: Feature dependencies are resolved automatically. If a feature depends on another, it will only be enabled if all its dependencies are enabled.

- **Extensibility**: The system supports future integration with external feature flag providers (e.g., LaunchDarkly, Unleash) and can be extended to support toggling via a database or admin UI.

## Example: feature_flags.yaml

```yaml
canbus:
  enabled: true
  core: true
  depends_on: []

web_ui:
  enabled: true
  core: true
  depends_on: []

# Add additional features below as needed
```

## Best Practices

- **Add new features** by editing `feature_flags.yaml`.
- **Enable/disable features at runtime** using environment variables or config files, not by editing YAML in production.
- **Document feature purpose and dependencies** in the YAML file and/or codebase.
- **Reload features** at runtime if your config changes (see `FeatureManager.reload_features_from_config`).

## See Also
- [backend/services/feature_manager.py](../../backend/services/feature_manager.py)
- [backend/services/feature_flags.yaml](../../backend/services/feature_flags.yaml)
- [Configuration and Environment Variables](../environment-variable-integration.md)
