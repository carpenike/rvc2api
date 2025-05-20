#!/usr/bin/env bash
# setup-vcan.sh — Set up virtual CAN interfaces (vcan0 & vcan1)

set -euxo pipefail

echo "🚗 Setting up virtual CAN interfaces..."

# 1) Ensure the vcan kernel module exists (dry-run)
if ! modprobe -n vcan >/dev/null 2>&1; then
  echo "⚠️  vcan kernel module not available; skipping vcan setup."
  exit 0
fi

# 2) If both interfaces already exist, nothing to do
if ip link show vcan0 &>/dev/null && ip link show vcan1 &>/dev/null; then
  echo "✅  vcan0 and vcan1 are already up"
  exit 0
fi

# 3) Load the module and create the interfaces
echo "🔧  Loading vcan module and creating interfaces..."
modprobe vcan
ip link add dev vcan0 type vcan
ip link add dev vcan1 type vcan

# 4) Bring them up
echo "🔧  Bringing up vcan0 & vcan1..."
ip link set up vcan0
ip link set up vcan1

echo "✅  vcan interfaces setup completed"
