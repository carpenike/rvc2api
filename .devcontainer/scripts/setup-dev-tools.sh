#!/bin/bash
# setup-dev-tools.sh - Set up development tools
# This script installs and configures development tools using Nix

# Exit on errors
set -e

echo "🔧 Setting up development tools..."

# Check if Nix is available
if ! command -v nix &>/dev/null; then
  echo "❌ Nix is not available. Cannot install development tools."
  exit 1
fi

echo "📦 Installing development tools via Nix..."

# Install core development tools
nix-env -iA \
  nixpkgs.git \
  nixpkgs.pre-commit \
  nixpkgs.direnv \
  nixpkgs.python3 \
  nixpkgs.nodejs_20 \
  nixpkgs.poetry \
  nixpkgs.ripgrep \
  nixpkgs.jq \
  nixpkgs.gnumake \
  || echo "⚠️ Some packages failed to install"

# Set up direnv
if command -v direnv &>/dev/null; then
  echo "🔧 Setting up direnv..."
  if ! grep -q "direnv hook" ~/.bashrc; then
    echo 'eval "$(direnv hook bash)"' >> ~/.bashrc
  fi

  if [ -f "/workspace/.envrc" ]; then
    cd /workspace && direnv allow || echo "⚠️ direnv allow failed (non-fatal)"
  fi
fi

# Set up pre-commit hooks
if [ -f "/workspace/.pre-commit-config.yaml" ]; then
  echo "🪝 Setting up pre-commit hooks..."
  cd /workspace && pre-commit install || echo "⚠️ pre-commit install failed (non-fatal)"
fi

# Set up Poetry environment
if [ -f "/workspace/pyproject.toml" ]; then
  echo "📝 Setting up Poetry environment..."
  cd /workspace && poetry env use python || echo "⚠️ Poetry environment setup failed (non-fatal)"
  cd /workspace && poetry install --no-root || echo "⚠️ Poetry install failed (non-fatal)"
fi

# Set up Node.js environment
if [ -f "/workspace/web_ui/package.json" ]; then
  echo "📝 Setting up Node.js environment..."
  cd /workspace/web_ui && npm install || echo "⚠️ npm install failed (non-fatal)"
fi

echo "✅ Development tools setup completed"
