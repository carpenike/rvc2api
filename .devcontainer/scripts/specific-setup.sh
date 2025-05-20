#!/usr/bin/env bash
# specific-setup.sh — Run project-specific setup tasks in the devcontainer

set -euo pipefail

LOG_FILE="/workspace/devcontainer_startup.log"
echo "🚀 Project-specific setup started at $(date)" > "$LOG_FILE"

# 1) Source single-user Nix profile if present
if [ -f "$HOME/.nix-profile/etc/profile.d/nix.sh" ]; then
  # shellcheck source=/dev/null
  . "$HOME/.nix-profile/etc/profile.d/nix.sh"
fi

# Ensure Nix binaries are in PATH
export PATH="$HOME/.nix-profile/bin:$PATH"

# 2) vCAN interface setup (non-fatal)
if [ -x /workspace/.devcontainer/scripts/setup-vcan.sh ]; then
  echo "🔧 Setting up vCAN interfaces…" | tee -a "$LOG_FILE"
  if ! sudo /workspace/.devcontainer/scripts/setup-vcan.sh >>"$LOG_FILE" 2>&1; then
    echo "⚠️ vCAN setup failed (non-fatal)" | tee -a "$LOG_FILE"
  fi
fi

# 3) Allow Git to safely work in a mounted workspace
git config --global --add safe.directory /workspace

# 4) Project dependencies (Poetry & npm)
echo "📦 Installing project dependencies…" | tee -a "$LOG_FILE"
cd /workspace

if [ -f pyproject.toml ]; then
  echo "📦 Poetry install…" | tee -a "$LOG_FILE"
  if ! poetry install; then
    echo "⚠️ Poetry install failed" | tee -a "$LOG_FILE"
  fi
fi

if [ -f web_ui/package.json ]; then
  echo "📦 npm ci (web_ui)…" | tee -a "$LOG_FILE"
  pushd web_ui >/dev/null
  if ! npm ci; then
    echo "⚠️ npm ci failed" | tee -a "$LOG_FILE"
  fi
  popd >/dev/null
fi

# 5) Enable direnv for the workspace
echo "🔧 Enabling direnv…" | tee -a "$LOG_FILE"
if ! direnv allow; then
  echo "⚠️ direnv allow failed (non-fatal)" | tee -a "$LOG_FILE"
fi

# 6) Create a helper for launching the Nix dev shell
cat > /workspace/.devcontainer/activate-nix-env.sh << 'EOF'
#!/usr/bin/env bash
set -euo pipefail
echo "🚀 Activating Nix development environment…"
cd /workspace
exec nix develop
EOF
chmod +x /workspace/.devcontainer/activate-nix-env.sh

echo "✅ Project-specific setup completed at $(date)" | tee -a "$LOG_FILE"
