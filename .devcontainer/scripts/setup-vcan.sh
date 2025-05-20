#!/bin/bash
# setup-vcan.sh - Set up virtual CAN interfaces
# This script ensures that virtual CAN interfaces are available

# Exit on errors
set -e

echo "🚗 Setting up virtual CAN interfaces..."

# Check if the can kernel module is available
if ! modprobe -n can; then
  echo "⚠️ CAN kernel module not available. Skipping vcan setup."
  exit 0
fi

# Check if vcan interfaces already exists
if ip link show vcan0 &>/dev/null && ip link show vcan1 &>/dev/null; then
  echo "✅ vcan0 and vcan1 interfaces already exist"
  exit 0
fi

# Create vcan interfaces
echo "Creating vcan0 and vcan1 interfaces..."
sudo modprobe vcan
sudo ip link add dev vcan0 type vcan
sudo ip link add dev vcan1 type vcan

# Bring up vcan interfaces
sudo ip link set up vcan0
sudo ip link set up vcan1

echo "✅ vcan interfaces setup completed"
