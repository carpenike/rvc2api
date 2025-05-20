#!/bin/bash
# post-start.sh - Run after container start
# Set up environment, tools, and configurations

# Exit on errors with stack trace
set -e
trap 'echo "Error on line $LINENO" >> "$LOG_FILE"' ERR

LOG_FILE="/workspace/devcontainer_startup.log"
echo "🚀 Post-start setup started at $(date)" > "$LOG_FILE"

# Make all scripts executable (ensure permissions after mounting)
find /workspace/.devcontainer -type f -name "*.sh" -exec chmod +x {} \;

echo "⚙️ Setting up development environment..." | tee -a "$LOG_FILE"

# Setup Components
components=(
  "Git configuration"
  "Direnv configuration"
  "Pre-commit hooks"
  "Poetry environment"
  "Node.js environment"
  "vCAN interfaces"
)

# 1. Set up and verify Nix
echo "🔧 Setting up Nix environment..." | tee -a "$LOG_FILE"
if command -v nix &>/dev/null; then
  echo "✅ Nix is available: $(nix --version)" | tee -a "$LOG_FILE"
else
  echo "⚠️ Nix is not available in PATH. Running diagnostics..." | tee -a "$LOG_FILE"
  /workspace/.devcontainer/diagnostics/diagnose-nix.sh >> "$LOG_FILE" 2>&1
fi

# 2. Git configuration
echo "🔄 Setting up Git..." | tee -a "$LOG_FILE"
git config --global --add safe.directory /workspace
git config --global core.autocrlf input
git config --global core.eol lf
echo "✅ Git configuration completed" | tee -a "$LOG_FILE"

# 3. Set up direnv if available
if command -v direnv &> /dev/null; then
  echo "📂 Setting up direnv..." | tee -a "$LOG_FILE"
  cd /workspace && direnv allow || echo "⚠️ direnv allow failed (non-fatal)" | tee -a "$LOG_FILE"
  # Add direnv hook to bashrc if not already there
  if ! grep -q "direnv hook" ~/.bashrc; then
    echo 'eval "$(direnv hook bash)"' >> ~/.bashrc
  fi
  echo "✅ direnv setup completed" | tee -a "$LOG_FILE"
fi

# 3.5. Set up Nix aliases and wrappers
echo "🔧 Setting up Nix wrappers and aliases..." | tee -a "$LOG_FILE"
/workspace/.devcontainer/scripts/setup-nix-aliases.sh >> "$LOG_FILE" 2>&1 || echo "⚠️ Nix aliases setup failed (non-fatal)" | tee -a "$LOG_FILE"
echo "✅ Nix wrappers setup completed" | tee -a "$LOG_FILE"

# 4. Pre-commit hooks setup
if [ -f "/workspace/.pre-commit-config.yaml" ]; then
  echo "🪝 Setting up pre-commit hooks..." | tee -a "$LOG_FILE"
  cd /workspace && pre-commit install 2>/dev/null || echo "⚠️ pre-commit install failed (non-fatal)" | tee -a "$LOG_FILE"
  echo "✅ Pre-commit hooks setup completed" | tee -a "$LOG_FILE"
fi

# 5. Set up Poetry environment if needed
if [ -f "/workspace/pyproject.toml" ] && command -v poetry &> /dev/null; then
  echo "📝 Setting up Poetry environment..." | tee -a "$LOG_FILE"
  cd /workspace && poetry env use python || echo "⚠️ Poetry environment setup failed (non-fatal)" | tee -a "$LOG_FILE"
  cd /workspace && poetry install --no-root || echo "⚠️ Poetry install failed (non-fatal)" | tee -a "$LOG_FILE"
  echo "✅ Poetry environment setup completed" | tee -a "$LOG_FILE"
fi

# 6. Set up Node.js environment if needed
if [ -f "/workspace/web_ui/package.json" ]; then
  echo "📝 Setting up Node.js environment..." | tee -a "$LOG_FILE"
  cd /workspace/web_ui && npm install || echo "⚠️ npm install failed (non-fatal)" | tee -a "$LOG_FILE"
  echo "✅ Node.js environment setup completed" | tee -a "$LOG_FILE"
fi

# 7. Set up vcan interfaces if needed
echo "🚗 Setting up virtual CAN interfaces..." | tee -a "$LOG_FILE"
if [ -f "/workspace/scripts/ensure_vcan_interfaces.sh" ]; then
  bash /workspace/scripts/ensure_vcan_interfaces.sh >> "$LOG_FILE" 2>&1 || echo "⚠️ vcan interface setup failed (non-fatal)" | tee -a "$LOG_FILE"
  echo "✅ vcan interface setup completed" | tee -a "$LOG_FILE"
else
  echo "⚠️ vcan interface setup script not found" | tee -a "$LOG_FILE"
fi

echo "✨ DevContainer setup completed successfully!" | tee -a "$LOG_FILE"
echo "📋 For detailed logs and diagnostics, see $LOG_FILE" | tee -a "$LOG_FILE"

# Create a success marker file
touch "/workspace/.devcontainer_ready"
