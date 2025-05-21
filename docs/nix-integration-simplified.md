# Simplified Nix Integration for rvc2api

This document explains the changes to the Nix integration in rvc2api:

## Key Changes

1. **Version Source of Truth**: Changed from `VERSION` file to `pyproject.toml`
   - The version is now extracted directly from `pyproject.toml` in `flake.nix`
   - The `VERSION` file has been removed as it's no longer needed

2. **Simplified Development Environment**:
   - Moved from a complex poetry2nix setup to a simpler direct Poetry approach
   - The `nix develop` shell now uses Poetry directly for dependency management
   - This avoids the numerous package override issues encountered with poetry2nix

3. **Workflow Improvements**:
   - Automatic Poetry virtualenv setup in the devShell
   - Proper library paths for native dependencies
   - Better shell experience with clear instructions
   - Simplified dependency management

## Benefits

- **Single Source of Truth**: Version information is now only maintained in `pyproject.toml`
- **Improved Reliability**: The development environment is more reliable and simpler to maintain
- **Reduced Complexity**: Fewer overrides and complex configurations
- **Better Developer Experience**: The shell setup is automatic and provides helpful information

## Using the Dev Environment

1. Enter the development shell:
   ```bash
   nix develop
   ```

2. Run Python commands through Poetry:
   ```bash
   poetry run python src/core_daemon/main.py
   poetry run pytest
   ```

3. Install additional dependencies:
   ```bash
   poetry add <package>
   ```

## How Versioning Works

1. The version is defined in `pyproject.toml` under `[tool.poetry].version`
2. For releases, this version is updated by release-please
3. The `flake.nix` reads this version using:
   ```nix
   version = let
     pyproject = builtins.fromTOML (builtins.readFile ./pyproject.toml);
   in pyproject.tool.poetry.version;
   ```

## Troubleshooting

If you encounter issues with the Nix environment:

1. Make sure you have the latest flake.nix and flake.lock by running:
   ```bash
   git pull
   ```

2. Reset the environment with:
   ```bash
   rm -rf .venv
   nix develop
   ```

3. For dependency issues, try updating Poetry's lock file:
   ```bash
   poetry update
   ```
