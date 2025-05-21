#!/usr/bin/env fish

# Script to set up initial versioned documentation
# Specifically designed for fish shell compatibility

echo "Setting up versioned documentation..."

# Check for mike installation
if not poetry run pip list | grep -q mike
    echo "Installing mike..."
    poetry run pip install mike
end

# Generate OpenAPI schema
echo "Generating OpenAPI schema..."
poetry run python scripts/export_openapi.py

# Get current version from pyproject.toml
set current_version (grep -m 1 "^version" pyproject.toml | cut -d= -f2 | tr -d ' "')
echo "Current version is: $current_version"

# Ensure gh-pages branch exists
if not git show-ref --verify --quiet refs/heads/gh-pages
    echo "Creating gh-pages branch..."
    git checkout --orphan gh-pages
    git rm -rf .
    touch .nojekyll
    echo "rvc2api Documentation" > index.html
    git add .nojekyll index.html
    git commit -m "Initial gh-pages commit"

    # Try pushing to origin, catch errors
    git push origin gh-pages; or begin
        echo "Failed to push gh-pages branch. You may need to create it on GitHub first."
        echo "Continuing with local setup..."
    end

    # Return to main branch
    git checkout main
end

# Deploy initial versions
echo "Deploying documentation versions..."

# Deploy current version
echo "Deploying version $current_version..."
poetry run mike deploy $current_version --push

# Deploy dev version
echo "Deploying dev version..."
poetry run mike deploy dev --push

# Set current version as default
echo "Setting version $current_version as default and latest..."
poetry run mike alias $current_version latest --push
poetry run mike set-default latest --push

echo "Documentation versioning setup complete!"
echo ""
echo "To view the versioned documentation locally, run:"
echo "poetry run mike serve"
