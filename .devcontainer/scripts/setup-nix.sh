#!/bin/bash
# setup-nix.sh - Set up Nix package manager
# This script installs Nix with proper optimizations for container environments

# Don't exit on errors but log them
set +e
trap 'echo "ERROR: Command failed with exit code $? at line $LINENO"' ERR

LOG_FILE="/workspace/nix_setup.log"
echo "🔧 Starting Nix setup at $(date)" > "$LOG_FILE"

# ============= HELPER FUNCTIONS =============
function log() {
  echo "$1" | tee -a "$LOG_FILE"
}

function log_cmd() {
  log "Running: $1"
  eval "$1" >> "$LOG_FILE" 2>&1
  return $?
}

# Helper: source Nix profile scripts for all shell types
source_nix_profiles() {
  # Bash/sh
  if [ -e /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh ]; then
    . /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh
  fi
  if [ -e "$HOME/.nix-profile/etc/profile.d/nix.sh" ]; then
    . "$HOME/.nix-profile/etc/profile.d/nix.sh"
  fi
  # Fish shell
  if [ -e "$HOME/.nix-profile/etc/profile.d/nix.fish" ]; then
    fish -c 'source $HOME/.nix-profile/etc/profile.d/nix.fish'
  fi
  # Zsh
  if [ -e "$HOME/.nix-profile/etc/profile.d/nix.zsh" ]; then
    zsh -c 'source $HOME/.nix-profile/etc/profile.d/nix.zsh'
  fi
  export PATH
}

# ============= MAIN SCRIPT =============
log "🔍 Checking if Nix is already installed..."

# Check if nix command exists
if command -v nix >/dev/null; then
  log "✅ Nix is already installed: $(nix --version)"
  source_nix_profiles
  exit 0
fi

# Check if Nix store directory exists
if [ -d "/nix/store" ]; then
  log "📋 Nix store exists, checking for binaries..."

  # Try to find nix binary in the store
  NIX_BIN=$(find /nix -name nix -type f -executable 2>/dev/null | grep -v "\.nix" | head -n 1)

  if [ -n "$NIX_BIN" ]; then
    log "✅ Found Nix binary at $NIX_BIN"
    NIX_DIR=$(dirname "$NIX_BIN")

    # Add to PATH temporarily and permanently
    export PATH="$NIX_DIR:$PATH"
    # Add to user shell init files if not already present
    for f in ~/.bashrc ~/.profile; do
      if ! grep -q "$NIX_DIR" "$f" 2>/dev/null; then
        echo "export PATH=$NIX_DIR:\$PATH" >> "$f"
      fi
    done
    # Add to /etc/profile.d for system-wide (if root)
    if [ "$(id -u)" = "0" ]; then
      echo "export PATH=$NIX_DIR:\$PATH" > /etc/profile.d/nix-path.sh
      chmod +x /etc/profile.d/nix-path.sh
    fi
    source_nix_profiles
    log "Testing Nix command..."
    if nix --version >/dev/null 2>&1; then
      log "✅ Nix is working: $(nix --version)"

      # Fix Nix configuration
      log "🔧 Setting up Nix configuration..."
      mkdir -p ~/.config/nix
      cat > ~/.config/nix/nix.conf << EOF
experimental-features = nix-command flakes
substituters = https://cache.nixos.org
trusted-public-keys = cache.nixos.org-1:6NCHdD59X431o0gWypbMrAURkbJ16ZPMQFGspcDShjY=
sandbox = relaxed
EOF
      exit 0
    fi
  fi
fi

# Need to install Nix from scratch
log "📦 Installing Nix from scratch..."

# Install dependencies
log "📦 Installing dependencies..."
log_cmd "sudo apt-get update"
log_cmd "sudo apt-get install -y curl xz-utils gnupg ca-certificates sudo"

# Ensure directories exist with proper permissions
log "🔧 Setting up Nix directories..."
log_cmd "sudo mkdir -p /nix"
log_cmd "sudo chown -R vscode:vscode /nix"
log_cmd "sudo chmod 755 /nix"

# Try single-user installation first (more reliable in containers)
log "📦 Installing Nix in single-user mode..."
curl -L https://nixos.org/nix/install | sh -s -- --no-daemon --yes

# Source the profile if installation was successful
if [ -e ~/.nix-profile/etc/profile.d/nix.sh ]; then
  log "🔧 Sourcing Nix profile..."
  source ~/.nix-profile/etc/profile.d/nix.sh
  source_nix_profiles

  # Test that Nix works
  if nix --version >/dev/null 2>&1; then
    log "✅ Nix installation successful: $(nix --version)"
  else
    log "❌ Nix installation completed but command not working"
  fi
else
  log "❌ Nix installation failed, profile script not found"

  # Try daemon installation as fallback
  log "🔄 Trying multi-user installation as fallback..."
  # Clean up any failed installation
  rm -rf ~/.nix-profile

  log_cmd "curl -L https://nixos.org/nix/install | sh -s -- --daemon --yes"

  # Source daemon profile if it exists
  if [ -e /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh ]; then
    log "🔧 Sourcing Nix daemon profile..."
    source /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh
    source_nix_profiles
  fi
fi

# Final check
if command -v nix >/dev/null; then
  log "✅ Nix is now available: $(nix --version)"

  # Setup Nix configuration
  log "🔧 Setting up Nix configuration..."
  mkdir -p ~/.config/nix
  cat > ~/.config/nix/nix.conf << EOF
experimental-features = nix-command flakes
substituters = https://cache.nixos.org
trusted-public-keys = cache.nixos.org-1:6NCHdD59X431o0gWypbMrAURkbJ16ZPMQFGspcDShjY=
sandbox = relaxed
EOF

  # Add Nix to shell initialization if not already there
  for f in ~/.bashrc ~/.profile; do
    if ! grep -q "nix-daemon.sh\|nix.sh" "$f" 2>/dev/null; then
      log "🔧 Adding Nix to $f..."
      echo 'if [ -e /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh ]; then . /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh; fi' >> "$f"
      echo 'if [ -e $HOME/.nix-profile/etc/profile.d/nix.sh ]; then . $HOME/.nix-profile/etc/profile.d/nix.sh; fi' >> "$f"
    fi
  done
  # Add to /etc/profile.d for system-wide (if root)
  if [ "$(id -u)" = "0" ]; then
    cat > /etc/profile.d/nix-path.sh << EOF
if [ -e /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh ]; then . /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh; fi
if [ -e $HOME/.nix-profile/etc/profile.d/nix.sh ]; then . $HOME/.nix-profile/etc/profile.d/nix.sh; fi
EOF
    chmod +x /etc/profile.d/nix-path.sh
  fi
  source_nix_profiles
  export PATH

  # Initialize channels if needed
  if ! nix-channel --list | grep -q "nixpkgs"; then
    log "🔧 Setting up Nix channels..."
    nix-channel --add https://nixos.org/channels/nixpkgs-unstable
    nix-channel --update
  fi

  log "✅ Nix setup completed successfully"
else
  log "❌ Nix installation failed after multiple attempts"
  exit 1
fi
