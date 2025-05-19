# MkDocs Versioning with Release-Please

This document explains how the documentation versioning system is integrated with our release process using release-please.

## Overview

We use a combination of tools to maintain versioned documentation that automatically stays in sync with our software releases:

1. **[mike](https://github.com/jimporter/mike)**: A versioning plugin for MkDocs that manages multiple versions of documentation
2. **[release-please](https://github.com/googleapis/release-please)**: Automates version bumps, changelog generation, and release creation
3. **GitHub Actions**: Automates the deployment of versioned documentation

This integration ensures that whenever a new version is released:

- A new documentation version is created with that version number
- The `VERSION` file is updated to reflect the new version
- Users can access both the latest and previous documentation versions

## How It Works

### Versioning Strategy

Documentation versions follow the same semantic versioning scheme as the codebase:

- `latest`: Always points to the most recent stable release
- `x.y.z`: Specific version numbers (e.g., `0.1.0`, `1.2.3`)
- `dev`: Development version (latest on the main branch)

### Automatic Version Updates

When changes are pushed to the main branch:

1. **release-please** analyzes commit messages to determine if a release is needed
2. If a release is created, release-please:

   - Creates a new version tag (e.g., `v1.2.3`)
   - Updates CHANGELOG.md
   - Updates version references in code
   - Updates the `VERSION` file with the new version number

3. The new tag triggers the `deploy-versioned-docs.yml` workflow, which:
   - Builds the documentation with the correct version number
   - Deploys it to GitHub Pages using mike
   - Sets the version as the default/latest if appropriate

### Manual Documentation Updates

Between releases, documentation updates are handled by:

1. The `deploy-docs.yml` workflow, which updates the `dev` version
2. This is triggered by changes to documentation files or manual workflow dispatch

## Working with Versioned Documentation

### Viewing Different Versions

The documentation site includes a version picker (typically in the header) that allows users to switch between different versions.

### Local Development

For local documentation development with versioning:

```bash
# Serve the documentation with live reloading (current working directory)
poetry run mkdocs serve

# Build and deploy a specific version locally
poetry run mike deploy 1.2.3

# Set a version as default
poetry run mike set-default 1.2.3 --push

# Deploy the dev version
poetry run mike deploy dev

# Serve the versioned documentation locally
poetry run mike serve
```

### VS Code Tasks

VS Code tasks are provided for common documentation versioning operations:

- **Docs: Serve Versioned Documentation**: Start a local mike server with versioned docs
- **Docs: Deploy Version**: Deploy a specific version (prompts for version)
- **Docs: List Versions**: List all currently deployed versions
- **Docs: Deploy Current Version**: Deploy using the version in the VERSION file
- **Docs: Set Default Version**: Set the version in VERSION file as default
- **Docs: Deploy Dev Version**: Deploy the current state as the "dev" version

## Configuration Details

### MkDocs Configuration

In `mkdocs.yml`, the mike plugin is configured:

```yaml
plugins:
  # Other plugins...
  - mike

extra:
  version:
    provider: mike
```

### GitHub Actions Workflows

- **release-please.yml**: Handles version bumping and release creation
- **deploy-versioned-docs.yml**: Deploys version-specific documentation when a new tag is created
- **deploy-docs.yml**: Updates the "dev" documentation between releases

### Integration with OpenAPI

The OpenAPI schema is automatically generated before building the documentation:

```yaml
- name: Generate OpenAPI schema
  run: |
    poetry run python scripts/export_openapi.py
```

This ensures that the API documentation is always up-to-date with the current version.

## Troubleshooting

### Common Issues

- **Missing Version in Dropdown**: Make sure the version was properly deployed with mike
- **Wrong Default Version**: Use `mike set-default` to correct it
- **Build Failures**: Check that the GitHub Actions workflow has the correct permissions

### Manually Deploying a Version

If needed, you can manually trigger the `deploy-versioned-docs.yml` workflow:

1. Go to Actions → Deploy Versioned Documentation → Run workflow
2. Enter the version number (without the 'v' prefix)
3. Choose whether to set it as the default

## Related Documentation

- [GitHub Pages Deployment](github-pages-deployment.md)
- [GitHub Actions Summary](github-actions-summary.md)
- [Documentation Organization](documentation-organization.md)
