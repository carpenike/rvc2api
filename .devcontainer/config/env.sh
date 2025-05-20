#!/bin/bash
# env.sh - Environment variables for the devcontainer
# This file is sourced by the lifecycle scripts

# Python configuration
export PYTHONPATH="${WORKSPACE_FOLDER}:${PYTHONPATH}"

# Node configuration
export NODE_OPTIONS="--openssl-legacy-provider"

# Nix configuration
export NIX_CONFIG="experimental-features = nix-command flakes
substituters = https://cache.nixos.org
trusted-public-keys = cache.nixos.org-1:6NCHdD59X431o0gWypbMrAURkbJ16ZPMQFGspcDShjY=
sandbox = relaxed"

# Path configuration
export PATH="/nix/var/nix/profiles/default/bin:/nix/store:/nix/var/nix/profiles/per-user/vscode/bin:/bin:/usr/bin:/usr/local/bin:${PATH}"

# Container flags
export DEVCONTAINER="true"
export WORKSPACE_FOLDER="${WORKSPACE_FOLDER:-/workspace}"

# Load custom environment variables if present
if [ -f "${WORKSPACE_FOLDER}/devcontainer.env" ]; then
  source "${WORKSPACE_FOLDER}/devcontainer.env"
fi
