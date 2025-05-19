# Documentation Versioning

rvc2api documentation uses version-specific documentation that matches the software releases. This approach ensures that users can access documentation that corresponds exactly to the version they are using.

## How Documentation Versioning Works

We use [mike](https://github.com/jimporter/mike), a versioning plugin for MkDocs, to manage multiple versions of our documentation. This allows:

- Documentation to be versioned alongside code releases
- Users to easily switch between different versions
- The latest version to be marked as the default
- Older versions to remain accessible

## Versioning Strategy

Documentation versions follow the same semantic versioning scheme as the codebase:

- `latest` - Always points to the most recent stable release
- `x.y.z` - Specific version numbers (e.g., `0.1.0`, `1.2.3`)
- `dev` - Development version (latest on the main branch)

## How Documentation is Released

Documentation is released automatically through our GitHub Actions workflows:

1. When a new version is released via release-please (e.g., tag `v1.2.3`):

   - The `deploy-versioned-docs.yml` workflow is triggered
   - It builds the documentation with the correct version number
   - It deploys the documentation to GitHub Pages under the specific version

2. For manual documentation updates between releases:
   - The `deploy-docs.yml` workflow updates the `dev` version
   - This happens whenever changes are pushed to the `main` branch

## Viewing Different Documentation Versions

When viewing the documentation site, you can use the version picker (typically in the header) to switch between different versions.

## For Maintainers: Manual Version Deployment

You can manually deploy a specific version of the documentation using the GitHub Actions workflow:

1. Go to the "Actions" tab in the repository
2. Select the "Deploy Versioned Documentation" workflow
3. Click "Run workflow"
4. Enter the version number (without the 'v' prefix, e.g., `1.2.3`)
5. Choose whether to set it as the default version
6. Click "Run workflow"

## Local Documentation Development

For local documentation development and testing with versioning:

```bash
# Install dependencies
poetry install

# Generate OpenAPI schema
poetry run python scripts/export_openapi.py

# Serve the documentation with live reloading (development version)
poetry run mkdocs serve

# Build a specific version locally
poetry run mike deploy 1.2.3 --push

# Set a version as default
poetry run mike set-default 1.2.3 --push

# Serve the versioned documentation locally
poetry run mike serve
```

## Integration with Release-Please

Our documentation versioning is integrated with [release-please](https://github.com/googleapis/release-please), which manages version numbers and the changelog. When release-please creates a new release:

1. It increments the version in the `VERSION` file
2. It creates a tag with the new version
3. The tag triggers the versioned documentation workflow
4. The documentation is built and deployed with the correct version number

This ensures that documentation versions always match released software versions.
