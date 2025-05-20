#!/bin/bash
# initialize.sh - Pre-container initialization script
# Run on the host before container creation

# Exit on any error
set -e

# Get workspace folder path
WORKSPACE_FOLDER="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
echo "🚀 Initializing development environment in ${WORKSPACE_FOLDER}..."

# Create necessary directories for Nix
mkdir -p "${WORKSPACE_FOLDER}/.devcontainer/nix-store"
mkdir -p "${WORKSPACE_FOLDER}/.devcontainer/nix-profile"
mkdir -p "${WORKSPACE_FOLDER}/.devcontainer/home-cache"

# Set directory permissions
chmod 755 "${WORKSPACE_FOLDER}/.devcontainer/nix-store"
chmod 755 "${WORKSPACE_FOLDER}/.devcontainer/nix-profile"
chmod 755 "${WORKSPACE_FOLDER}/.devcontainer/home-cache"

# Remove previous status files
rm -f "${WORKSPACE_FOLDER}/.devcontainer_ready"
rm -f "${WORKSPACE_FOLDER}/devcontainer_startup.log"

echo "✅ Initialization complete"
