#!/bin/bash
# fix-nix-errors.sh - Fix common Nix file existence errors

set -e

LOG_FILE="/workspace/nix_fix.log"
echo "🔧 Starting Nix error fixes at $(date)" > "$LOG_FILE"

# Function to log messages
log() {
  echo "$1" | tee -a "$LOG_FILE"
}

# Check if we're running as root
if [ "$(id -u)" -ne 0 ]; then
  log "⚠️ This script should be run with sudo"
  exit 1
fi

# Fix for the specific 'File exists' error with iptables library
PROBLEM_FILE="/nix/store/gwwi7h74zh72414r50q99pnrqgi86l5s-iptables-1.8.11/lib/xtables/libip6t_hl.so"
PROBLEM_DIR=$(dirname "$PROBLEM_FILE")

if [ -f "$PROBLEM_FILE" ]; then
  log "🔧 Fixing file exists error for $PROBLEM_FILE"
  # Move the existing file out of the way
  mv "$PROBLEM_FILE" "$PROBLEM_FILE.bak"
  log "✅ Moved existing file to $PROBLEM_FILE.bak"
fi

# Create directory if it doesn't exist (in case the paths changed)
if [ ! -d "$PROBLEM_DIR" ]; then
  log "🔧 Creating directory $PROBLEM_DIR"
  mkdir -p "$PROBLEM_DIR"
fi

log "✅ Fix completed. Try running 'nix develop' again."
