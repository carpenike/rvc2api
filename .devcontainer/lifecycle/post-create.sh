#!/bin/bash
# post-create.sh - Run after container creation
# Set up development tools and environment

# Exit on any error
set -e

LOG_FILE="/workspace/devcontainer_startup.log"
echo "🚀 Post-creation setup started at $(date)" >> "$LOG_FILE"

# Setup Nix configuration for better performance
echo "🔧 Setting up optimized Nix configuration..." | tee -a "$LOG_FILE"
/workspace/.devcontainer/scripts/setup-nix-config.sh >> "$LOG_FILE" 2>&1 || {
  echo "⚠️ Nix configuration setup failed. See $LOG_FILE for details." | tee -a "$LOG_FILE"
}

# Install development tools if Nix is available
if command -v nix &>/dev/null; then
  echo "📦 Installing development tools via Nix..." | tee -a "$LOG_FILE"
  nix-env -iA nixpkgs.git nixpkgs.pre-commit nixpkgs.direnv || {
    echo "⚠️ Nix package installation failed. See $LOG_FILE for details." | tee -a "$LOG_FILE"
  }
else
  echo "⚠️ Nix not available, skipping package installation" | tee -a "$LOG_FILE"
fi

git config --global gpg.program /bin/gpg

# Make diagnostics scripts executable
chmod +x /workspace/.devcontainer/diagnostics/diagnose-nix.sh

echo "✅ Post-create setup completed successfully" | tee -a "$LOG_FILE"
