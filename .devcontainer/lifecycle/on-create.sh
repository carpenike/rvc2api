#!/bin/bash
# on-create.sh - Run when container is created
# Install essential system packages and prepare the environment

# Exit on any error
set -e

LOG_FILE="/workspace/devcontainer_startup.log"
echo "🚀 Container creation started at $(date)" > "$LOG_FILE"

# Make all scripts in the .devcontainer directory executable
find /workspace/.devcontainer -type f -name "*.sh" -exec chmod +x {} \;

echo "📦 Installing essential system packages..." | tee -a "$LOG_FILE"
sudo apt-get update
sudo apt-get install -y coreutils findutils procps util-linux sudo bash \
  curl wget git ca-certificates gnupg lsb-release

# Configure sudo
echo "🔧 Configuring sudo for non-password access..." | tee -a "$LOG_FILE"
echo "vscode ALL=(ALL) NOPASSWD:ALL" | sudo tee /etc/sudoers.d/vscode > /dev/null

# Fix ownership
echo "🔧 Fixing directory permissions..." | tee -a "$LOG_FILE"
sudo chown -R vscode:vscode /workspace

# Install Nix with proper error handling
echo "🔧 Setting up Nix package manager..." | tee -a "$LOG_FILE"
/workspace/.devcontainer/scripts/setup-nix.sh >> "$LOG_FILE" 2>&1 || {
  echo "⚠️ Nix installation failed. See $LOG_FILE for details." | tee -a "$LOG_FILE"
  echo "⚠️ Running Nix diagnostics..." | tee -a "$LOG_FILE"
  /workspace/.devcontainer/diagnostics/diagnose-nix.sh >> "$LOG_FILE" 2>&1
}

# Verify Nix installation
if command -v nix &>/dev/null; then
  echo "✅ Nix successfully installed: $(nix --version)" | tee -a "$LOG_FILE"
else
  echo "⚠️ Nix not available in PATH. Container may need to be rebuilt." | tee -a "$LOG_FILE"
fi

echo "✅ Container creation completed successfully" | tee -a "$LOG_FILE"
