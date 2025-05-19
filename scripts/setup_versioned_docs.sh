#!/usr/bin/env bash

# Script to set up initial versioned documentation
# Standard bash script for cross-platform compatibility

# Better error handling
set -e          # Exit on error
set -o pipefail # Exit on pipe failure

echo "Setting up versioned documentation..."

# Check for mike installation by trying to import it (with error suppression)
if ! poetry run python -c "import mike" 2>/dev/null; then
    echo "Installing mike..."
    poetry run pip install mike 2>/dev/null || true
fi

# Generate OpenAPI schema
echo "Generating OpenAPI schema..."
poetry run python scripts/export_openapi.py

# Get current version from pyproject.toml
current_version=$(grep -m 1 "^version" pyproject.toml | cut -d= -f2 | tr -d ' "')
echo "Current version is: $current_version"

# Ensure gh-pages branch exists
if ! git show-ref --verify --quiet refs/heads/gh-pages; then
    echo "Creating gh-pages branch..."
    git checkout --orphan gh-pages
    git rm -rf .
    touch .nojekyll
    echo "rvc2api Documentation" > index.html
    git add .nojekyll index.html
    git commit -m "Initial gh-pages commit"

    # Try pushing to origin, catch errors
    if ! git push origin gh-pages; then
        echo "Failed to push gh-pages branch. You may need to create it on GitHub first."
        echo "Continuing with local setup..."
    fi

    # Return to main branch
    git checkout main
fi

# Deploy initial versions
echo "Deploying documentation versions..."

# Deploy current version
echo "Deploying version $current_version..."
poetry run mike deploy "$current_version" --push --update-aliases latest

# Deploy dev version
echo "Deploying dev version..."
poetry run mike deploy dev --push

# Set current version as default
echo "Setting version $current_version as default..."
poetry run mike set-default latest --push

echo "Documentation versioning setup complete!"
echo ""
echo "To view the versioned documentation locally, run:"
echo "poetry run mike serve"
