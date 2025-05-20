#!/bin/bash
# setup-nix-config.sh - Setup Nix configuration for better performance

set -e

# Ensure directories exist
mkdir -p ~/.config/nix

# Copy our optimized configuration
cp /workspace/.devcontainer/nix.conf ~/.config/nix/nix.conf

echo "✅ Nix configuration set up for optimal performance"
