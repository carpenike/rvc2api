# Guide to MkDocs Versioning with Release-Please

This guide explains how to use the integrated MkDocs versioning system that works with release-please.

## Integration Summary

We have successfully integrated:

1. **MkDocs with the mike plugin**: For versioned documentation management
2. **release-please**: For automated version management and version updates in pyproject.toml
3. **GitHub Actions workflows**: For automated documentation deployment
4. **VS Code tasks**: For local development and testing

## Key Components

- `pyproject.toml`: Source of truth for the current version of the project
- `mike` plugin: Manages documentation versions
- `deploy-versioned-docs.yml`: Workflow for versioned documentation releases
- `deploy-docs.yml`: Workflow for development documentation updates
- `release-please.yml`: Workflow for automated version management

## How to Use the Versioning System

### Local Development

1. **View the current documentation**:

   ```bash
   poetry run mkdocs serve
   ```

2. **View versioned documentation**:

   ```bash
   # Using the VS Code task
   # "Docs: Serve Versioned Documentation"

   # Or manually
   ./scripts/docs_version.sh serve
   ```

3. **Deploy a specific version**:

   ```bash
   # Using the VS Code task
   # "Docs: Deploy Current Version"

   # Or manually
   ./scripts/docs_version.sh deploy

   # This automatically reads the version from pyproject.toml
   ```

4. **Set the default version**:

   ```bash
   # Using the VS Code task
   # "Docs: Set Default Version"

   # Or manually
   ./scripts/docs_version.sh set-default

   # This automatically reads the version from pyproject.toml
   ```

### Automated Deployment

1. **Development updates**:

   - Push changes to documentation files on the `main` branch
   - The `deploy-docs.yml` workflow will deploy the changes to the `dev` version

2. **Version releases**:
   - Use conventional commit messages (e.g., `feat: add new feature`)
   - When release-please creates a new version tag
   - The `deploy-versioned-docs.yml` workflow will deploy the documentation for that version

## Testing the Integration

To verify that the integration is working correctly:

1. **Check that versioned documentation is available**:

   - Run `poetry run mike list` to see all deployed versions
   - If no versions are available, run `./scripts/setup_versioned_docs.fish`

2. **Test a documentation update**:

   - Make a small change to a documentation file
   - Push to the `main` branch
   - Verify that the change appears in the `dev` version

3. **Test a version release**:
   - Make a commit with a conventional commit message
   - Push to the `main` branch
   - When release-please creates a new version
   - Verify that the new version is available in the version selector

## Troubleshooting

If you encounter issues with the versioning system:

1. **Check that the version in pyproject.toml is correct**:

   - The version should be in the format `version = "x.y.z"` under `[tool.poetry]`
   - release-please should update this automatically on releases

2. **Check permissions on bash scripts**:

   - Make sure the scripts are executable: `chmod +x scripts/*.sh`
   - If not, make them executable and try again

3. **Check that the gh-pages branch exists**:

   - If not, create it with the setup script: `./scripts/setup_versioned_docs.sh`

4. **Check the GitHub Actions logs**:
   - Look for errors in the workflows
   - Fix any issues and rerun the workflows

For detailed troubleshooting, see [Verifying Versioned Documentation](verifying-versioned-documentation.md).
