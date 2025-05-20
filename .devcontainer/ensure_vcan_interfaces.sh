#!/bin/bash
# ensure_vcan_interfaces.sh - Checks and creates vcan interfaces if needed
#
# This script is meant to be run from within the devcontainer
# It checks for vcan interfaces and creates them if they don't exist
#
# Usage:
#   ./scripts/ensure_vcan_interfaces.sh

set -e  # Exit on error

echo "🔍 Checking for vcan interfaces..."

# Check for vcan module
if ! lsmod | grep -q "^vcan "; then
    echo "⚠️ vcan module is not loaded."
    echo "🔧 Trying to load vcan module..."
    sudo modprobe vcan || { echo "❌ Failed to load vcan module. You may need to install kernel headers and recompile it."; exit 1; }
    echo "✅ vcan module loaded."
else
    echo "✅ vcan module is loaded."
fi

# Check and create vcan0
if ! ip link show vcan0 &>/dev/null; then
    echo "⚠️ vcan0 interface does not exist."
    echo "🔧 Creating vcan0 interface..."
    sudo ip link add dev vcan0 type vcan || { echo "❌ Failed to create vcan0 interface."; exit 1; }
    sudo ip link set up vcan0 || { echo "❌ Failed to bring up vcan0 interface."; exit 1; }
    echo "✅ vcan0 interface created and brought up."
else
    echo "✅ vcan0 interface exists."
    # Make sure vcan0 is up
    if ! ip link show vcan0 | grep -q "UP"; then
        echo "⚠️ vcan0 is down. Bringing it up..."
        sudo ip link set up vcan0 || { echo "❌ Failed to bring up vcan0 interface."; exit 1; }
        echo "✅ vcan0 brought up."
    fi
fi

# Check and create vcan1
if ! ip link show vcan1 &>/dev/null; then
    echo "⚠️ vcan1 interface does not exist."
    echo "🔧 Creating vcan1 interface..."
    sudo ip link add dev vcan1 type vcan || { echo "❌ Failed to create vcan1 interface."; exit 1; }
    sudo ip link set up vcan1 || { echo "❌ Failed to bring up vcan1 interface."; exit 1; }
    echo "✅ vcan1 interface created and brought up."
else
    echo "✅ vcan1 interface exists."
    # Make sure vcan1 is up
    if ! ip link show vcan1 | grep -q "UP"; then
        echo "⚠️ vcan1 is down. Bringing it up..."
        sudo ip link set up vcan1 || { echo "❌ Failed to bring up vcan1 interface."; exit 1; }
        echo "✅ vcan1 brought up."
    fi
fi

# Show interface details
echo "📊 vcan interface details:"
ip -details link show vcan0
ip -details link show vcan1

echo "🏁 vcan interface verification completed!"

# Check if can-utils is installed
if command -v cansend &> /dev/null; then
    echo "✅ can-utils is installed."
    echo "💡 You can test the vcan interfaces with commands like:"
    echo "   cansend vcan0 123#DEADBEEF"
    echo "   candump vcan0"
else
    echo "⚠️ can-utils is not installed. Installing now..."
    sudo apt-get update && sudo apt-get install -y can-utils
    if [ $? -eq 0 ]; then
        echo "✅ can-utils installed."
        echo "💡 You can test the vcan interfaces with commands like:"
        echo "   cansend vcan0 123#DEADBEEF"
        echo "   candump vcan0"
    else
        echo "❌ Failed to install can-utils. You can try installing it manually."
    fi
fi
