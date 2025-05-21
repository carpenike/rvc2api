# Version Management

This document explains how version management works in the rvc2api project.

## Single Source of Truth

The project uses a single source of truth for version information:

- **pyproject.toml**: Contains the canonical version number in the `[tool.poetry].version` field.

This approach simplifies version management by centralizing the version information in one place and aligning with Poetry's native versioning system.

## Version Updates

The project uses [release-please](https://github.com/googleapis/release-please) to manage version updates:

1. **Automated Updates**: When PRs are merged with conventional commits, release-please automatically:
   - Determines the appropriate version bump (major, minor, patch)
   - Updates the version in pyproject.toml
   - Creates a release PR with a changelog

2. **Version Extraction**: Various tools and scripts extract the version from pyproject.toml when needed:
   - `flake.nix` gets the version from pyproject.toml for building packages
   - Documentation versioning scripts read the version from pyproject.toml
   - The Python code uses `importlib.metadata.version("rvc2api")` to access the version at runtime

## Version Propagation

The version from pyproject.toml propagates through the system:

1. **At Build Time**: The version is included in the Python package metadata
2. **At Runtime**: The version is available via `importlib.metadata` or the `_version.py` module
3. **In Documentation**: MkDocs versioning uses the version for documentation releases

## Benefits

This approach provides several benefits:

- **Simplicity**: Only one place to update the version
- **Consistency**: All components share the same version information
- **Automation**: Release-please manages version changes according to semantic versioning
- **Integration**: Works well with Poetry, Nix, and documentation tools

## Previous Approach

Before this change, the project used both pyproject.toml and a separate VERSION file. This dual-source approach was eliminated to simplify version management and remove the risk of version inconsistencies.
