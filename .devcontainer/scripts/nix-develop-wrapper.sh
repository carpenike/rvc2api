#!/bin/bash
# nix-develop-wrapper.sh - A wrapper for 'nix develop' that handles common errors

LOG_FILE="/workspace/nix_develop.log"
echo "🚀 Running nix develop wrapper at $(date)" > "$LOG_FILE"

# Function to log messages
log() {
  echo "$1" | tee -a "$LOG_FILE"
  echo "$1"
}

log "🔧 Ensuring optimal Nix configuration..."
mkdir -p ~/.config/nix
cp -f /workspace/.devcontainer/nix.conf ~/.config/nix/nix.conf

log "🚀 Running nix develop..."
nix develop "$@" 2> >(tee -a /tmp/nix_error.log)

# Check if there was an error
if [ $? -ne 0 ]; then
  ERROR_LOG=$(cat /tmp/nix_error.log)

  # Check for the specific 'File exists' error
  if echo "$ERROR_LOG" | grep -q "File exists"; then
    log "⚠️ Detected 'File exists' error. Attempting to fix..."

    # Run the fix script with sudo
    sudo /workspace/.devcontainer/scripts/fix-nix-errors.sh

    # Try again
    log "🔄 Retrying nix develop..."
    nix develop "$@"
    exit $?
  else
    # If it's a different error
    log "❌ Error running nix develop: See $LOG_FILE for details"
    echo "$ERROR_LOG" >> "$LOG_FILE"
    exit 1
  fi
fi
