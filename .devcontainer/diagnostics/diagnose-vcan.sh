#!/bin/bash
# diagnose-vcan.sh - Diagnose vCAN interface issues

echo "🔍 Running vCAN diagnostics..."

# Check if CAN kernel module is loaded
echo "Checking kernel modules..."
if lsmod | grep can; then
  echo "✅ CAN kernel module is loaded"
else
  echo "❌ CAN kernel module is not loaded"
fi

# Check if vcan kernel module is loaded
if lsmod | grep vcan; then
  echo "✅ vCAN kernel module is loaded"
else
  echo "❌ vCAN kernel module is not loaded"
fi

# Check for vcan interfaces
echo "Checking vcan interfaces..."
if ip link show vcan0 &>/dev/null; then
  echo "✅ vcan0 interface exists"
  ip -details link show vcan0
else
  echo "❌ vcan0 interface does not exist"
fi

if ip link show vcan1 &>/dev/null; then
  echo "✅ vcan1 interface exists"
  ip -details link show vcan1
else
  echo "❌ vcan1 interface does not exist"
fi

# Check user permissions for can interfaces
echo "Checking user permissions..."
if getent group | grep -q "^docker:"; then
  echo "✅ docker group exists"
  if id -nG | grep -q docker; then
    echo "✅ Current user is in docker group"
  else
    echo "❌ Current user is not in docker group"
  fi
else
  echo "❌ docker group does not exist"
fi

echo "🔍 vCAN diagnostics completed"
