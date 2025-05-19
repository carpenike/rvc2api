#!/bin/bash

# Check if vcan kernel module is available
if ! lsmod | grep -q vcan; then
    echo "Loading vcan kernel module..."
    modprobe vcan || echo "Failed to load vcan module. This might not be supported in the VM kernel."
fi

# Set up virtual CAN interface if module is loaded
if lsmod | grep -q vcan; then
    echo "Setting up vcan0 interface..."
    ip link add dev vcan0 type vcan 2>/dev/null || echo "vcan0 may already exist"
    ip link set up vcan0 || echo "Failed to bring up vcan0"
    echo "Setting up vcan1 interface..."
    ip link add dev vcan1 type vcan 2>/dev/null || echo "vcan1 may already exist"
    ip link set up vcan1 || echo "Failed to bring up vcan1"
    echo "Virtual CAN interfaces:"
    ip -details link show vcan0
    ip -details link show vcan1
else
    echo "WARNING: vcan module not loaded. Virtual CAN interfaces not available."
    echo "Your application may need to use alternative test methods."
fi

# Continue with normal execution
exec "$@"
