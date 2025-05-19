# Documentation Versioning Fixes

This document provides information about fixes applied to the documentation versioning system.

## Standardized Bash Scripts and pyproject.toml

To improve compatibility and standardize the project, the documentation versioning scripts have been converted from fish shell to bash, and the source of truth for version information has been moved from the `VERSION` file to `pyproject.toml`.

### 1. Bash-Compatible Scripts

We've converted all scripts to standard bash syntax for better cross-platform compatibility:

```bash
# New standard bash script
#!/usr/bin/env bash

# Get the current version from pyproject.toml
function get_version() {
    # Extract version from pyproject.toml using grep and cut
    version=$(grep -m 1 "^version" pyproject.toml | cut -d= -f2 | tr -d ' "')
    echo "$version"
}
```

### 2. Using pyproject.toml as Source of Truth

Instead of relying on a separate `VERSION` file, we now extract the version directly from `pyproject.toml`:

```bash
# Extract version from pyproject.toml
current_version=$(grep -m 1 "^version" pyproject.toml | cut -d= -f2 | tr -d ' "')
```

### 3. Mike Command Flags

The `--rebase` flag was causing issues with the `mike` command. We've removed it to ensure compatibility:

```bash
# Original problematic command
poetry run mike deploy --push --rebase $version

# Fixed command
poetry run mike deploy --push "$current_version"
```

### 4. VS Code Tasks

The VS Code tasks have been updated to use standard bash syntax:

```json
{
  "label": "Docs: Deploy Current Version",
  "command": "cd ${workspaceFolder} && ./scripts/docs_version.sh deploy"
}
```

## How to Use the New Scripts

### Setup Initial Versioning

If you're setting up versioning for the first time:

```bash
./scripts/setup_versioned_docs.sh
```

This script:

1. Generates the OpenAPI schema
2. Creates the gh-pages branch if it doesn't exist
3. Deploys the current version (from pyproject.toml)
4. Deploys the development version
5. Sets the current version as default

### Day-to-Day Versioning Tasks

For regular versioning tasks, use the helper script:

```bash
# View all available versions
./scripts/docs_version.sh list

# Deploy the current version
./scripts/docs_version.sh deploy

# Serve the versioned documentation locally
./scripts/docs_version.sh serve
```

### VS Code Tasks

VS Code tasks have been updated to use the standardized bash scripts:

- **Docs: Serve Versioned Documentation**: Start a local mike server
- **Docs: List Versions**: List all deployed versions
- **Docs: Deploy Current Version**: Deploy using the version in pyproject.toml
- **Docs: Set Default Version**: Set the version in pyproject.toml as default
- **Docs: Deploy Dev Version**: Deploy the current state as "dev"

## GitHub Actions Workflow

The GitHub Actions workflow has been updated to remove the `--rebase` flag and to extract the version from pyproject.toml when needed:

```yaml
# Set version from tag, input, or pyproject.toml
if [ "${{ github.event_name }}" = "workflow_dispatch" ] && [ -n "${{ github.event.inputs.version }}" ]; then
  # Use manually specified version from workflow dispatch
  VERSION="${{ github.event.inputs.version }}"
elif [ "${{ github.event_name }}" != "workflow_dispatch" ]; then
  # Extract version from tag
  VERSION=${GITHUB_REF#refs/tags/v}
else
  # Extract from pyproject.toml as fallback
  VERSION=$(grep -m 1 "^version" pyproject.toml | cut -d= -f2 | tr -d ' "')
fi
```

## Integration with release-please

The versioning system now integrates seamlessly with release-please:

1. release-please updates the version in `pyproject.toml`
2. The documentation versioning scripts read from `pyproject.toml`
3. When a new release is created by release-please, the versioned documentation is automatically published

## Troubleshooting

If you encounter any issues:

1. **Permission denied when executing scripts**: Make sure the scripts are executable: `chmod +x scripts/docs_version.sh scripts/setup_versioned_docs.sh`
2. **Error extracting version from pyproject.toml**: Ensure the version is properly formatted in pyproject.toml with `version = "x.y.z"` format

3. **Error with the --rebase flag**: Remove this flag from mike commands.

4. **GitHub Pages branch issues**: Make sure you've run the setup script correctly and have appropriate permissions to push to gh-pages.

5. **Command sequence in fish shell**: Use `and` instead of `&&` when you want to chain commands in a VS Code task for fish shell.

See [Verifying Versioned Documentation](verifying-versioned-documentation.md) for more troubleshooting steps.
