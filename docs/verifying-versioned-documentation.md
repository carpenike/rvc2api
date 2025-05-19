# Verifying Documentation Versioning

This document provides instructions for verifying that the documentation versioning system is working correctly.

## Prerequisites

Before proceeding, ensure you have:

1. Set up the repository according to the [development environment](development-environments.md) guidelines
2. Installed all the required dependencies with `poetry install`
3. Configured git for the repository

## Initial Setup Verification

To verify that the initial setup for versioned documentation is complete:

```bash
# List all currently deployed versions
poetry run mike list
```

You should see at least:

- `dev` - The development version
- The current version number (e.g., `0.1.0`)
- `latest` - An alias to the current version

If these versions are not present, you can set them up:

```bash
# Using the setup script (fish shell)
./scripts/setup_versioned_docs.fish

# Alternatively, using VS Code tasks
# Run the "Docs: Setup Initial Versioned Documentation" task
```

## Testing Local Versioned Documentation

To test that versioned documentation works locally:

```bash
# Start the versioned documentation server
poetry run mike serve
```

Visit http://localhost:8000/ and verify:

1. The version selector shows the available versions
2. You can switch between versions
3. The content matches the expected version

## Testing Version Deployment

To test deploying a specific version:

```bash
# Deploy the current version
poetry run mike deploy $(cat VERSION | tr -d '\n')

# Or for fish shell
set current_version (cat VERSION | string trim); and poetry run mike deploy $current_version
```

Verify that the version is correctly listed:

```bash
poetry run mike list
```

## Integration with Release-Please

To verify that the integration with release-please is working:

1. Make a commit with a conventional commit message (e.g., `feat: add new feature`)
2. Push to the main branch
3. Check that the release-please workflow creates a pull request for version bump
4. Once merged, verify that the new version is deployed to the documentation site

## Common Issues and Solutions

### Missing Version in Dropdown

If a version is not appearing in the dropdown:

```bash
# Check if the version exists
poetry run mike list

# If missing, deploy it
poetry run mike deploy <version> --push
```

### Wrong Default Version

If the wrong version is set as default:

```bash
# Set the correct default version
poetry run mike set-default <version> --push
```

### Build Failures

If the documentation build fails:

1. Check the GitHub Actions logs for errors
2. Verify that the OpenAPI schema generation works locally
3. Ensure all dependencies are correctly installed

## Maintaining Documentation Versions

As a best practice:

1. Always test documentation changes locally before pushing
2. Use the `dev` version for ongoing work
3. Only deploy specific versions when a release is created
4. Use the GitHub Actions workflows for production deployments
