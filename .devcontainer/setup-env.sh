#!/bin/bash
# filepath: /Users/ryan/src/rvc2api/.devcontainer/setup-env.sh
set -e

echo "🚀 Setting up optimized development environment for Colima..."

# Create directories for caching
mkdir -p ~/.cache/pip
mkdir -p ~/.npm
mkdir -p ~/.nix-store

# 1. Configure Nix for better performance
echo "⚙️ Optimizing Nix configuration..."
mkdir -p ~/.config/nix

cat > ~/.config/nix/nix.conf <<EOF
experimental-features = nix-command flakes
substituters = https://cache.nixos.org
trusted-public-keys = cache.nixos.org-1:6NCHdD59X431o0gWypbMrAURkbJ16ZPMQFGspcDShjY=
sandbox = relaxed
max-jobs = auto
cores = 0
# Colima-specific optimization for Nix
extra-system-features = nixos-test benchmark big-parallel kvm
EOF

# 2. Check for CAN interfaces (should be configured on Colima host via systemd)
echo "🔌 Checking CAN interfaces..."
interfaces=$(ls -la /sys/class/net/ 2>/dev/null | grep -E "vcan[0-9]+" || true)

if [ -z "$interfaces" ]; then
  echo "⚠️ No vcan interfaces detected in container. This is normal if:"
  echo "  - Container was just started (may need to wait for systemd)"
  echo "  - You're not using host network mode (required for CAN access)"
  echo ""
  echo "Note: vcan interfaces should already be configured on the Colima host via systemd."
  echo "See the COLIMA.md guide for details on setting up vcan interfaces if needed."
else
  echo "✅ Found virtual CAN interfaces:"
  for interface in $(echo "$interfaces" | awk '{print $9}'); do
    ip -details link show "$interface" 2>/dev/null || echo "Cannot show details for $interface"
  done
fi

# 3. Configure caching for better Colima performance
echo "📦 Optimizing package caching for Colima..."
# Node.js cache configuration
npm config set cache ~/.npm --global

# Python pip cache
pip config set global.cache-dir ~/.cache/pip

# 4. Configure Git for large repositories
echo "🔄 Optimizing Git configuration..."
git config --global core.compression 9
git config --global http.postBuffer 1048576000
# Specific Git optimizations for macOS/Colima filesystem performance
git config --global core.preloadindex true
git config --global core.fscache true

# 5. File system optimizations
echo "💾 Applying filesystem optimizations..."
# Touch a marker file to test file system performance
dd if=/dev/zero of=~/fs_test_file bs=1M count=10 2>/dev/null
rm ~/fs_test_file
echo "File system write performance check completed"

# 6. Display system information
echo "💻 System Information:"
echo "CPU: $(nproc) cores available"
grep "MemTotal" /proc/meminfo
echo "Docker Runtime: Colima"
echo "Operating System: $(cat /etc/os-release | grep PRETTY_NAME | cut -d '"' -f 2)"

echo "✅ Colima-optimized development environment setup complete!"
